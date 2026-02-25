import os
import random
from ortools.sat.python import cp_model

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    print("WARNING: ezdxf not installed. Will mock the output.")

def optimize_layout(equipment_list, space_width=50, space_height=50):
    """
    OR-Tools를 이용하여 변전소 내 전기기기 배치를 최적화합니다.
    - 장비들이 공간을 벗어나지 않도록 제약
    - 장비 간 겹치지 않도록 제약
    - 유지보수/이격거리(안전거리) 기본값 부여
    """
    model = cp_model.CpModel()
    
    # 각 장비의 X, Y 좌표 (bottom-left)
    x_vars = {}
    y_vars = {}
    
    # 2D 겹침 방지를 위한 Interval 변수
    x_intervals = []
    y_intervals = []
    
    for eq in equipment_list:
        name = eq["name"]
        w = eq["width"]
        h = eq["height"]
        clearance = eq.get("clearance", 2)  # 안전 이격거리
        
        # 도면 공간 내 제약조건 (0 ~ 공간크기 - 장비크기)
        x_vars[name] = model.NewIntVar(0, space_width - w, f'x_{name}')
        y_vars[name] = model.NewIntVar(0, space_height - h, f'y_{name}')
        
        # 겹침 방지를 위해 (장비 크기 + 이격거리) 만큼의 가상 상자 생성
        x_interval = model.NewFixedSizeIntervalVar(x_vars[name], w + clearance, f'x_interval_{name}')
        y_interval = model.NewFixedSizeIntervalVar(y_vars[name], h + clearance, f'y_interval_{name}')
        
        x_intervals.append(x_interval)
        y_intervals.append(y_interval)

    # 2D 직사각형들이 서로 겹치지 않도록 하는 핵심 제약 (NoOverlap2D)
    model.AddNoOverlap2D(x_intervals, y_intervals)
    
    # 목표: 전체를 최대한 왼쪽 하단(0,0)에 밀착 배치 (비용 최소화 연산)
    # OR-Tools SAT 은 최적화보다는 만족(Satisfiability)에 강력하지만, 
    # 간단한 목적함수로 패킹 밀도를 높일 수 있음.
    model.Minimize(sum(x_vars.values()) + sum(y_vars.values()))

    # 솔버 실행
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for eq in equipment_list:
            name = eq["name"]
            results.append({
                "name": name,
                "x": solver.Value(x_vars[name]),
                "y": solver.Value(y_vars[name]),
                "width": eq["width"],
                "height": eq["height"]
            })
        return results
    else:
        return None

def generate_cad_dxf(layout_data, output_file="substation_layout.dxf"):
    """
    ezdxf 라브러리를 사용해 2D CAD(DXF) 포맷의 도면을 직접 생성합니다.
    """
    if not EZDXF_AVAILABLE:
        print("ezdxf is required to generate the actual DXF file.")
        return False
        
    doc = ezdxf.new('R2010')  # AutoCAD 2010 DXF format
    msp = doc.modelspace()
    
    # 도면 테두리 그리기 (50x50 공간)
    msp.add_lwpolyline([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)], dxfattribs={'color': 1}) # Red border
    
    # 최적화된 좌표 바탕으로 기기 배치
    for item in layout_data:
        x, y = item["x"], item["y"]
        w, h = item["width"], item["height"]
        
        # 기기 외함(Bounding Box) 그리기
        msp.add_lwpolyline([(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)], 
                           dxfattribs={'color': 3}) # Green rect
        
        # 기기 이름 텍스트 추가
        text_x = x + (w/2) - (len(item["name"]) * 0.3)
        text_y = y + (h/2) - 0.5
        msp.add_text(item["name"], dxfattribs={'height': 1.0}).set_placement((text_x, text_y))
    
    doc.saveas(output_file)
    print(f"✅ CAD 파일 생성 완료: {output_file}")
    return True

if __name__ == "__main__":
    print("⚡ [초기화] 154kV 변전소 기기 리스트 및 안전 이격거리 파싱 중...")
    # LLM이 파싱해준 설계 사양이라고 가정
    equipment_specs = [
        {"name": "M_TR_150MVA", "width": 8, "height": 10, "clearance": 3},
        {"name": "GIS_170kV", "width": 12, "height": 6, "clearance": 2},
        {"name": "SWG_25.8kV", "width": 15, "height": 5, "clearance": 2},
        {"name": "Condenser", "width": 5, "height": 5, "clearance": 1},
        {"name": "ESS_Battery", "width": 10, "height": 8, "clearance": 2},
        {"name": "Control_Panel", "width": 6, "height": 3, "clearance": 1}
    ]
    
    print("📐 [연산] OR-Tools를 이용한 규정 기반 최적 배치 연산 시작...")
    layout_result = optimize_layout(equipment_specs, space_width=45, space_height=35)
    
    if layout_result:
        print("🎯 [성공] 최적 배치 좌표 도출 완료:")
        for r in layout_result:
            print(f"  - [{r['name']}] 위치: X={r['x']}, Y={r['y']} (크기: {r['width']}x{r['height']})")
            
        print("✍️ [출력] AutoCAD 호환 도면(.dxf) 생성 중...")
        generate_cad_dxf(layout_result)
    else:
        print("❌ [실패] 주어진 공간 내(45x35)에 이격거리 규정을 맞추어 배치할 수 없습니다.")

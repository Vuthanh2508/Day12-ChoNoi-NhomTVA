#!/usr/bin/env python3
"""Script kiểm định tính hợp lệ của File Kho theo Contract G v1.3 (AI Skill: inventory-validator).

Quy tắc Contract G v1.3:
1. File JSON chỉ có khóa gốc duy nhất là 'items'.
2. Trong Contract v1.3, 'items' bắt buộc là mảng các đối tượng cá thể: [{"id": "...", "kind": "...", "fresh": ...}].
3. 'id' là chuỗi không rỗng, các id không được trùng lặp.
4. 'kind' thuộc danh mục cho phép: 'ca_loc', 'ca_linh', 'bong_dien_dien', 'bong_sung', 'ca_keo', 'keo_neo'.
5. 'fresh' là số thực/nguyên trong đoạn [0, 100]. Cá thể có fresh >= 30 mới được tính là tồn khả dụng (dưới 30 là ươn/spoiled).
6. Từ chối định dạng kho đếm cũ v1.0 (dạng dict {"items": {kind: count}}).
7. Phân tích số món ăn tối đa có thể nấu được theo Menu 6 món chuẩn của quán.
"""

import json
import os
import sys

ALLOWED_KINDS = {"ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo"}

MENU = {
    "ca_loc_nuong_trui": {"ca_loc": 1},
    "goi_bong_sung": {"bong_sung": 2},
    "lau_ca_linh_dien_dien": {"ca_linh": 3, "bong_dien_dien": 1},
    "canh_chua_ca_loc": {"ca_loc": 1, "bong_dien_dien": 1},
    "ca_keo_nuong": {"ca_keo": 2},
    "lau_mam": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
}


def validate_inventory_file(path: str):
    if not os.path.exists(path):
        return False, f"File không tồn tại: {path}", {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Lỗi đọc định dạng JSON: {e}", {}

    if not isinstance(data, dict):
        return False, "Nội dung gốc phải là một JSON object.", {}

    if set(data.keys()) != {"items"}:
        return False, f"File kho chỉ được có duy nhất khóa 'items', đang có: {list(data.keys())}", {}

    items = data["items"]
    counts = {}

    if isinstance(items, list):
        seen_ids = set()
        spoiled_count = 0
        for i, it in enumerate(items):
            if not isinstance(it, dict) or set(it.keys()) != {"id", "kind", "fresh"}:
                return False, f"Item {i} không đúng cấu trúc {{id, kind, fresh}}", {}
            item_id = it.get("id")
            if not isinstance(item_id, str) or not item_id:
                return False, f"Item {i}: id phải là chuỗi khác rỗng", {}
            if item_id in seen_ids:
                return False, f"ID bị trùng lặp: '{item_id}'", {}
            seen_ids.add(item_id)
            kind = it.get("kind")
            if kind not in ALLOWED_KINDS:
                return False, f"Nguyên liệu lạ không thuộc danh mục cho phép: '{kind}'", {}
            fresh = it.get("fresh")
            if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or fresh < 0 or fresh > 100:
                return False, f"Độ tươi của item {item_id} phải trong [0, 100], đang là: {fresh!r}", {}
            if fresh >= 30:
                counts[kind] = counts.get(kind, 0) + 1
            else:
                spoiled_count += 1
        msg = f"Hợp đồng kho cá thể v1.3 hợp lệ (Contract G v1.3 compliant). Tổng: {len(items)} cá thể ({len(items) - spoiled_count} tươi, {spoiled_count} ươn < 30)."
        return True, msg, counts

    elif isinstance(items, dict):
        return False, "Contract v1.3 không chấp nhận định dạng kho đếm theo loại (v1.0); bắt buộc sử dụng mảng cá thể [{'id', 'kind', 'fresh'}, ...].", {}

    return False, "'items' bắt buộc phải là mảng các cá thể trong Contract v1.3.", {}


def analyze_menu(items: dict):
    dish_counts = {}
    for dish_id, recipe in MENU.items():
        max_possible = min(items.get(k, 0) // needed for k, needed in recipe.items())
        dish_counts[dish_id] = max_possible
    return dish_counts


def main():
    if len(sys.argv) < 2:
        print("Cách dùng: python validate_inventory.py <đường_dẫn_file_kho.json>")
        return 2

    path = sys.argv[1]
    ok, msg, items = validate_inventory_file(path)

    print("=" * 50)
    print(f"KIỂM ĐỊNH FILE KHO CHUẨN CONTRACT G v1.3: {path}")
    print("=" * 50)

    if not ok:
        print(f"❌ THẤT BẠI: {msg}")
        return 2

    print(f"✅ THÀNH CÔNG: {msg}")
    print(f"📦 Số nguyên liệu khả dụng (fresh >= 30): {items}")

    dishes = analyze_menu(items)
    print("\n🍽️  Khả năng phục vụ Menu của Quán:")
    for dish_id, count in dishes.items():
        status = f"✅ Nấu được tối đa {count} suất" if count > 0 else "❌ Không đủ nguyên liệu"
        print(f"  - {dish_id}: {status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

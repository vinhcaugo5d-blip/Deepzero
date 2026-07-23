# src/cluster_router.py
import httpx
import asyncio
from typing import List, Dict

class CloudNode:
    def __init__(self, name: str, url: str, is_backup: bool = False):
        self.name = name
        self.url = url
        self.is_backup = is_backup
        self.is_alive = True

class MultiServerRouter:
    def __init__(self):
        self.nodes: List[CloudNode] = []

    def add_node(self, name: str, url: str, is_backup: bool = False):
        """Thêm một máy chủ mới vào danh sách quản lý"""
        self.nodes.append(CloudNode(name, url, is_backup))

    async def ping_node(self, node: CloudNode):
        """Kiểm tra phản hồi thực tế của máy chủ"""
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                res = await client.get(f"{node.url}/health")
                node.is_alive = (res.status_code == 200)
            except Exception:
                node.is_alive = False

    def get_optimal_node(self) -> CloudNode:
        """Chọn máy chủ chính còn sống -> Tự động chuyển máy chủ dự phòng nếu máy chính sập"""
        # Ưu tiên lấy máy chủ chính đang hoạt động
        primaries = [n for n in self.nodes if n.is_alive and not n.is_backup]
        if primaries:
            return primaries[0]

        # Nếu máy chính sập, kích hoạt máy chủ dự phòng (Backup Node)
        backups = [n for n in self.nodes if n.is_alive and n.is_backup]
        if backups:
            print("[Router Warning] Máy chủ chính mất kết nối! Tự động chuyển sang máy chủ DỰ PHÒNG...")
            return backups[0]

        raise RuntimeError("Tất cả máy chủ trong hệ thống cụm đều bị đứt kết nối!")

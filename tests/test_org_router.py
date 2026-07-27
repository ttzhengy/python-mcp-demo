"""OrgIdRouter 单元测试。

覆盖场景：
  - 映射中的 orgId 返回对应 baseurl
  - 不在映射中的 orgId 返回 default_url
  - None / 空字符串返回 default_url
  - URL 尾部斜杠自动移除
  - get_supported_org_ids 返回正确集合
"""

from __future__ import annotations

import pytest

from python_mcp_demo.attendance.router import OrgIdRouter


@pytest.fixture
def router() -> OrgIdRouter:
    """创建测试用路由器实例。"""
    return OrgIdRouter(
        mapping={
            "A": "http://srv-a:8080",
            "B": "http://srv-b:8080/",  # 故意带尾部斜杠
            "C": "http://srv-c:8080",
        },
        default_url="http://default:8080/",
    )


class TestOrgIdRouter:
    """OrgIdRouter 路由测试。"""

    def test_resolve_known_org_id(self, router: OrgIdRouter) -> None:
        """映射中的 orgId 返回对应 baseurl。"""
        assert router.resolve("A") == "http://srv-a:8080"
        assert router.resolve("C") == "http://srv-c:8080"

    def test_resolve_trailing_slash_stripped(self, router: OrgIdRouter) -> None:
        """URL 尾部斜杠应被自动移除。"""
        assert router.resolve("B") == "http://srv-b:8080"
        assert router.resolve(None) == "http://default:8080"

    def test_resolve_unknown_org_id_returns_default(self, router: OrgIdRouter) -> None:
        """不在映射中的 orgId 返回 default_url。"""
        assert router.resolve("X") == "http://default:8080"
        assert router.resolve("Z") == "http://default:8080"

    def test_resolve_none_returns_default(self, router: OrgIdRouter) -> None:
        """org_id 为 None 时返回 default_url。"""
        assert router.resolve(None) == "http://default:8080"

    def test_resolve_empty_string_returns_default(self, router: OrgIdRouter) -> None:
        """org_id 为空字符串时返回 default_url。"""
        assert router.resolve("") == "http://default:8080"

    def test_get_supported_org_ids(self, router: OrgIdRouter) -> None:
        """返回所有支持的 orgId 集合。"""
        expected = {"A", "B", "C"}
        assert router.get_supported_org_ids() == expected

    def test_empty_mapping(self) -> None:
        """空映射时所有 orgId 都返回 default_url。"""
        r = OrgIdRouter(mapping={}, default_url="http://fallback:9090")
        assert r.resolve("A") == "http://fallback:9090"
        assert r.get_supported_org_ids() == set()

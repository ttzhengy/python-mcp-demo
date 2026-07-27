"""考勤模块 OrgId 路由器。

根据 orgId 参数动态选择对应的后端 baseurl，支持多租户/多环境路由。
映射关系在配置中定义，运行时不可变。
"""

from __future__ import annotations

from python_mcp_demo.core.log import logger


class OrgIdRouter:
    """OrgId → BaseURL 路由器。

    将固定的 orgId 集合映射到不同的后端服务地址。
    映射关系在初始化时一次性加载，运行时不可变。

    Args:
        mapping: orgId → baseurl 的映射字典。
        default_url: 当 orgId 不在映射中时使用的默认 baseurl。

    Example:
        >>> router = OrgIdRouter(
        ...     mapping={"A": "http://srv-a:8080", "B": "http://srv-b:8080"},
        ...     default_url="http://srv-default:8080",
        ... )
        >>> router.resolve("A")
        'http://srv-a:8080'
        >>> router.resolve("X")
        'http://srv-default:8080'
    """

    def __init__(
        self,
        mapping: dict[str, str],
        default_url: str,
    ) -> None:
        """初始化路由器。

        Args:
            mapping: orgId → baseurl 映射字典。
            default_url: 默认 baseurl（orgId 不在映射中时使用）。
        """
        self._mapping = mapping.copy()
        self._default_url = default_url.rstrip("/")
        # 规范化所有 URL：移除尾部斜杠
        self._mapping = {k: v.rstrip("/") for k, v in self._mapping.items()}
        logger.debug(
            "OrgIdRouter 初始化: {count} 个映射, default={default}",
            count=len(self._mapping),
            default=self._default_url,
        )

    def resolve(self, org_id: str | None) -> str:
        """根据 orgId 解析对应的 baseurl。

        Args:
            org_id: 组织 ID（如 "A"、"B"、"C"）。

        Returns:
            对应的 baseurl（已移除尾部斜杠）。
        """
        if not org_id:
            return self._default_url
        base_url = self._mapping.get(org_id, self._default_url)
        logger.debug(
            "OrgIdRouter.resolve: org_id={org_id} → {base_url}",
            org_id=org_id,
            base_url=base_url,
        )
        return base_url

    def get_supported_org_ids(self) -> set[str]:
        """返回所有支持的 orgId 集合。

        Returns:
            支持的 orgId 集合。
        """
        return set(self._mapping.keys())

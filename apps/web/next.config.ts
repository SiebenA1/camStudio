import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 允许通过局域网 IP 访问 dev server 时正常使用 HMR（否则跨域被拦截）
  allowedDevOrigins: ["172.18.144.1", "localhost", "127.0.0.1"],
  // 隐藏 Next.js 开发指示器（左下角浮动按钮）：它会遮挡侧边栏，且其面板为英文内置 UI 无法本地化。
  // 如需恢复：删掉此行，或改为 devIndicators: { position: "bottom-right" }。
  devIndicators: false,
};

export default nextConfig;

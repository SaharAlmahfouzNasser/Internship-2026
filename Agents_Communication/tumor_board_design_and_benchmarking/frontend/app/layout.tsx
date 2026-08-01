import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Tumor Board Stream",
  description: "Streaming presentation UI for the two-agent oncology assignment"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

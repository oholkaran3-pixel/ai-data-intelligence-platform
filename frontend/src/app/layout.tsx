import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Data Intelligence Platform',
  description: 'Autonomous Enterprise Data Analytics, Multi-Agent AI & Reporting Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}

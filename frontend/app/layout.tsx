import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

// Force dynamic rendering to avoid SSG issues with Supabase
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Fresh Solver OR-Tools Scheduling System',
  description: 'Production scheduling data entry system with Supabase integration',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div style={{ padding: '2rem' }}>
          <h1>DEPLOYMENT TEST - NO PROVIDERS</h1>
          <p>If you see this, the layout is working without providers.</p>
          <hr />
          {children}
        </div>
      </body>
    </html>
  );
}
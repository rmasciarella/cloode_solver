import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { AppProviders } from '@/lib/providers/app-providers-simple';

const inter = Inter({ subsets: ['latin'] });

// Force dynamic rendering to avoid SSG issues with Supabase
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Vulcan MES - Manufacturing Execution System',
  description: 'Production scheduling and manufacturing execution system with Supabase integration',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppProviders>
          {children}
        </AppProviders>
      </body>
    </html>
  );
}
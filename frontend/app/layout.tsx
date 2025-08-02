import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { AppProviders } from '@/lib/providers/app-providers-simple';

const inter = Inter({ subsets: ['latin'] });

// Only force dynamic for routes that actually need it
// Static routes like dashboard and form pages can use SSG/ISR
export const dynamic = 'auto'

export const metadata: Metadata = {
  title: 'Vulcan MES - Manufacturing Execution System',
  description: 'Production scheduling and manufacturing execution system with Supabase integration',
  keywords: ['manufacturing', 'MES', 'production scheduling', 'OR-Tools', 'optimization'],
  authors: [{ name: 'Vulcan MES Team' }],
  openGraph: {
    title: 'Vulcan MES - Manufacturing Execution System',
    description: 'Advanced production scheduling and manufacturing execution system',
    type: 'website',
  },
  robots: {
    index: false, // Don't index in development
    follow: false,
  },
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
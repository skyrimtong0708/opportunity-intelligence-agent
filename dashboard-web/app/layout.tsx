import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://opportunity-intelligence-control-center.manhtd0708.chatgpt.site'),
  title: 'Opportunity Intelligence — Control Center',
  description: 'Evidence-led opportunity discovery across five focused niches.',
  openGraph: {
    title: 'Opportunity Intelligence — Control Center',
    description: 'Real evidence. Better decisions across five focused opportunity niches.',
    images: ['/og.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Opportunity Intelligence — Control Center',
    description: 'Real evidence. Better decisions across five focused opportunity niches.',
    images: ['/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Analytics Dashboard',
  description: 'Track email campaign performance with real-time analytics. Monitor open rates, click rates, conversions, and get AI-powered insights.',
};

export default function AnalyticsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

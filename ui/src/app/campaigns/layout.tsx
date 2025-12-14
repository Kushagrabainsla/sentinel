import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Email Campaigns',
  description: 'Create, manage, and optimize your email marketing campaigns with Sentinel. Track performance, A/B test, and boost engagement.',
};

export default function CampaignsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

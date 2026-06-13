import IntelCardClient from './client';

export async function generateStaticParams() {
  return Array.from({ length: 104 }, (_, i) => ({ id: String(i + 1) }));
}

export default function IntelCardPage() {
  return <IntelCardClient />;
}

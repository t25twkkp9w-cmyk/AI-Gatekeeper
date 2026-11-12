import './globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'AI Gatekeeper Agent | Healthcare Governance', description: 'A synthetic healthcare AI governance workflow with evidence, controls and human review.' };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }

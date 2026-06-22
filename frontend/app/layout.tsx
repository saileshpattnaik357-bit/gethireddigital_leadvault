import type { Metadata } from 'next'
import './styles.css'

export const metadata: Metadata = {
  title: 'LeadVault',
  description: 'Agentic AI lead mining engine',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

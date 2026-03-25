import './globals.css'

export const metadata = {
  title: 'Kostructure - AWS Cost Estimator',
  description: 'Estimate AWS infrastructure costs from Terraform files',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

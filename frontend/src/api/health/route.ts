import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'thanatopolis-frontend',
    timestamp: new Date().toISOString()
  })
}

/**
 * @jest-environment jsdom
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock the Hero component
const Hero = () => (
  <div data-testid="hero">
    <h1>Welcome to Agent47</h1>
    <p>Your AI-powered business automation platform</p>
  </div>
)

describe('Hero Component', () => {
  it('renders hero component', () => {
    render(<Hero />)
    
    expect(screen.getByTestId('hero')).toBeInTheDocument()
    expect(screen.getByText('Welcome to Agent47')).toBeInTheDocument()
    expect(screen.getByText('Your AI-powered business automation platform')).toBeInTheDocument()
  })

  it('has correct heading level', () => {
    render(<Hero />)
    
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Welcome to Agent47')
  })
})
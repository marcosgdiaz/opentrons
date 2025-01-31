import * as React from 'react'

import { COLORS, renderWithProviders } from '@opentrons/components'

import { Chip } from '..'

const render = (props: React.ComponentProps<typeof Chip>) => {
  return renderWithProviders(<Chip {...props} />)
}

describe('Chip', () => {
  let props: React.ComponentProps<typeof Chip>

  it('should render text, no icon with basic colors', () => {
    props = {
      text: 'mockBasic',
      type: 'basic',
    }
    const [{ getByTestId, getByText, queryByLabelText }] = render(props)
    const chip = getByTestId('Chip_basic')
    const chipText = getByText('mockBasic')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.darkBlack20)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.darkBlack90)}`)
    expect(queryByLabelText('icon_mockBasic')).not.toBeInTheDocument()
  })

  it('should render text, icon, bgcolor with success colors', () => {
    props = {
      text: 'mockSuccess',
      type: 'success',
    }
    const [{ getByTestId, getByText, getByLabelText }] = render(props)
    const chip = getByTestId('Chip_success')
    const chipText = getByText('mockSuccess')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.green3)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.green1)}`)
    const icon = getByLabelText('icon_mockSuccess')
    expect(icon).toHaveStyle(`color: ${String(COLORS.green1)}`)
  })

  it('should render text, icon, no bgcolor with success colors and bg false', () => {
    props = {
      background: false,
      text: 'mockSuccess',
      type: 'success',
    }
    const [{ getByTestId, getByText, getByLabelText }] = render(props)
    const chip = getByTestId('Chip_success')
    const chipText = getByText('mockSuccess')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.transparent)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.green1)}`)
    const icon = getByLabelText('icon_mockSuccess')
    expect(icon).toHaveStyle(`color: ${String(COLORS.green1)}`)
  })

  it('should render text, icon, bgcolor with warning colors', () => {
    props = {
      text: 'mockWarning',
      type: 'warning',
    }
    const [{ getByTestId, getByText, getByLabelText }] = render(props)
    const chip = getByTestId('Chip_warning')
    const chipText = getByText('mockWarning')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.yellow3)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.yellow1)}`)
    const icon = getByLabelText('icon_mockWarning')
    expect(icon).toHaveStyle(`color: ${String(COLORS.yellow1)}`)
  })

  it('should render text, icon, no bgcolor with warning colors and bg false', () => {
    props = {
      background: false,
      text: 'mockWarning',
      type: 'warning',
    }
    const [{ getByTestId, getByText, getByLabelText }] = render(props)
    const chip = getByTestId('Chip_warning')
    const chipText = getByText('mockWarning')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.transparent)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.yellow1)}`)
    const icon = getByLabelText('icon_mockWarning')
    expect(icon).toHaveStyle(`color: ${String(COLORS.yellow1)}`)
  })

  it('should render text, icon, bgcolor with neutral colors', () => {
    props = {
      text: 'mockNeutral',
      type: 'neutral',
    }
    const [{ getByTestId, getByText, getByLabelText }] = render(props)
    const chip = getByTestId('Chip_neutral')
    const chipText = getByText('mockNeutral')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.darkBlack20)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.darkBlack70)}`)
    const icon = getByLabelText('icon_mockNeutral')
    expect(icon).toHaveStyle(`color: ${String(COLORS.darkBlack90)}`)
  })

  it('should render text, icon, no bgcolor with neutral colors and bg false', () => {
    props = {
      background: false,
      text: 'mockNeutral',
      type: 'neutral',
    }
    const [{ getByTestId, getByText, getByLabelText }] = render(props)
    const chip = getByTestId('Chip_neutral')
    const chipText = getByText('mockNeutral')
    expect(chip).toHaveStyle(`background-color: ${String(COLORS.transparent)}`)
    expect(chipText).toHaveStyle(`color: ${String(COLORS.darkBlack70)}`)
    const icon = getByLabelText('icon_mockNeutral')
    expect(icon).toHaveStyle(`color: ${String(COLORS.darkBlack90)}`)
  })
})

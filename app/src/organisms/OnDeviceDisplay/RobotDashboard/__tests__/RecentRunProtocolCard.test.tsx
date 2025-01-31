import * as React from 'react'
import { fireEvent } from '@testing-library/react'
import { formatDistance } from 'date-fns'
import { when, resetAllWhenMocks } from 'jest-when'
import { MemoryRouter } from 'react-router-dom'

import { renderWithProviders } from '@opentrons/components'
import { useAllRunsQuery } from '@opentrons/react-api-client'

import { i18n } from '../../../../i18n'
import { useMissingProtocolHardware } from '../../../../pages/Protocols/hooks'
import { useTrackProtocolRunEvent } from '../../../Devices/hooks'
import { useTrackEvent } from '../../../../redux/analytics'
import { useCloneRun } from '../../../ProtocolUpload/hooks'
import { useMissingHardwareText } from '../hooks'
import { RecentRunProtocolCard } from '../'

import type { ProtocolHardware } from '../../../../pages/Protocols/hooks'

jest.mock('@opentrons/react-api-client')
jest.mock('../../../../pages/Protocols/hooks')
jest.mock('../../../../organisms/Devices/hooks')
jest.mock('../../../../organisms/RunTimeControl/hooks')
jest.mock('../../../../organisms/ProtocolUpload/hooks')
jest.mock('../../../../redux/analytics')
jest.mock('../hooks')

const mockProtocolName = 'mockProtocol'
const mockProtocolId = 'mockProtocolId'
const mockLastRun = '2023-04-12T21:30:49.124108+00:00'
const RUN_ID = 'mockRunId'

const mockMissingPipette = [
  {
    hardwareType: 'pipette',
    pipetteName: 'p1000_single_gen3',
    mount: 'left',
    connected: false,
  },
] as ProtocolHardware[]

const mockMissingModule = [
  {
    hardwareType: 'module',
    moduleModel: 'temperatureModuleV2',
    slot: '1',
    connected: false,
  },
] as ProtocolHardware[]

const missingBoth = [
  {
    hardwareType: 'pipette',
    pipetteName: 'p1000_single_gen3',
    mount: 'left',
    connected: false,
  },
  {
    hardwareType: 'module',
    moduleModel: 'temperatureModuleV2',
    slot: '1',
    connected: false,
  },
] as ProtocolHardware[]

const mockRunData = {
  id: RUN_ID,
  createdAt: '2022-05-03T21:36:12.494778+00:00',
  completedAt: 'thistime',
  startedAt: 'thistime',
  protocolId: 'mockProtocolId',
} as any

let mockCloneRun: jest.Mock

const mockUseMissingProtocolHardware = useMissingProtocolHardware as jest.MockedFunction<
  typeof useMissingProtocolHardware
>
const mockUseAllRunsQuery = useAllRunsQuery as jest.MockedFunction<
  typeof useAllRunsQuery
>
const mockUseTrackProtocolRunEvent = useTrackProtocolRunEvent as jest.MockedFunction<
  typeof useTrackProtocolRunEvent
>
const mockUseTrackEvent = useTrackEvent as jest.MockedFunction<
  typeof useTrackEvent
>
const mockUseCloneRun = useCloneRun as jest.MockedFunction<typeof useCloneRun>
const mockUseMissingHardwareText = useMissingHardwareText as jest.MockedFunction<
  typeof useMissingHardwareText
>

const render = (props: React.ComponentProps<typeof RecentRunProtocolCard>) => {
  return renderWithProviders(
    <MemoryRouter>
      <RecentRunProtocolCard {...props} />
    </MemoryRouter>,
    {
      i18nInstance: i18n,
    }
  )
}

let mockTrackEvent: jest.Mock
let mockTrackProtocolRunEvent: jest.Mock

describe('RecentRunProtocolCard', () => {
  let props: React.ComponentProps<typeof RecentRunProtocolCard>

  beforeEach(() => {
    props = {
      protocolName: mockProtocolName,
      protocolId: mockProtocolId,
      lastRun: mockLastRun,
      runId: RUN_ID,
    }
    mockTrackEvent = jest.fn()
    mockTrackProtocolRunEvent = jest.fn(
      () => new Promise(resolve => resolve({}))
    )
    mockUseMissingHardwareText.mockReturnValue('Ready to run')
    mockUseTrackEvent.mockReturnValue(mockTrackEvent)
    mockUseMissingProtocolHardware.mockReturnValue([])
    mockUseAllRunsQuery.mockReturnValue({
      data: { data: [mockRunData] },
    } as any)
    when(mockUseTrackProtocolRunEvent).calledWith(RUN_ID).mockReturnValue({
      trackProtocolRunEvent: mockTrackProtocolRunEvent,
    })
    mockCloneRun = jest.fn()
    when(mockUseCloneRun)
      .calledWith(RUN_ID, expect.anything())
      .mockReturnValue({ cloneRun: mockCloneRun, isLoading: false })
  })

  afterEach(() => {
    resetAllWhenMocks()
    jest.clearAllMocks()
  })

  it('should render text', () => {
    const [{ getByText }] = render(props)
    const lastRunTime = formatDistance(new Date(mockLastRun), new Date(), {
      addSuffix: true,
    }).replace('about ', '')
    getByText('Ready to run')
    getByText('mockProtocol')
    getByText(`Last run ${lastRunTime}`)
  })

  it('should render missing chip when missing a pipette', () => {
    mockUseMissingProtocolHardware.mockReturnValue(mockMissingPipette)
    mockUseMissingHardwareText.mockReturnValue('Missing 1 pipette')
    const [{ getByText }] = render(props)
    getByText('Missing 1 pipette')
  })

  it('should render missing chip when missing a module', () => {
    mockUseMissingProtocolHardware.mockReturnValue(mockMissingModule)
    mockUseMissingHardwareText.mockReturnValue('Missing 1 module')
    const [{ getByText }] = render(props)
    getByText('Missing 1 module')
  })

  it('should render missing chip (module and pipette) when missing a pipette and a module', () => {
    mockUseMissingProtocolHardware.mockReturnValue(missingBoth)
    mockUseMissingHardwareText.mockReturnValue('Missing hardware')
    const [{ getByText }] = render(props)
    getByText('Missing hardware')
  })

  it('when tapping a card, mock functions is called', () => {
    const [{ getByLabelText }] = render(props)
    const button = getByLabelText('RecentRunProtocolCard')
    fireEvent.click(button)
    expect(mockTrackEvent).toHaveBeenCalledWith({
      name: 'proceedToRun',
      properties: { sourceLocation: 'RecentRunProtocolCard' },
    })
    expect(mockTrackProtocolRunEvent).toBeCalledWith({ name: 'runAgain' })
  })
})

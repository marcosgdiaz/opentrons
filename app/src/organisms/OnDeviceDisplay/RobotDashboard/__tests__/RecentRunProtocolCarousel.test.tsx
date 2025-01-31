import * as React from 'react'

import { renderWithProviders } from '@opentrons/components'
import { useAllRunsQuery } from '@opentrons/react-api-client'

import { RecentRunProtocolCard, RecentRunProtocolCarousel } from '..'

import type { ProtocolResource } from '@opentrons/shared-data'

jest.mock('@opentrons/react-api-client')
jest.mock('../RecentRunProtocolCard')

const mockSortedProtocol = [
  {
    analysisSummaries: [],
    createdAt: '2023-04-11T00:44:20.669922+00:00',
    files: [
      {
        name: 'Mock Protocol',
        role: '',
      },
    ],
    id: 'mockSortedProtocolID',
    key: 'mockKey',
    metadata: {
      author: 'New API User',
      description: 'mock protocol',
      name: 'Mock Protocol',
    },
    robotType: 'OT-3 Standard',
    protocolType: 'python',
  },
] as ProtocolResource[]

const mockRun = {
  actions: [],
  completedAt: '2023-04-12T15:14:13.811757+00:00',
  createdAt: '2023-04-12T15:13:52.110602+00:00',
  current: false,
  errors: [],
  id: '853a3fae-8043-47de-8f03-5d28b3ee3d35',
  labware: [],
  labwareOffsets: [],
  liquids: [],
  modules: [],
  pipettes: [],
  protocolId: 'mockSortedProtocolID',
  status: 'stopped',
}

const mockRecentRunProtocolCard = RecentRunProtocolCard as jest.MockedFunction<
  typeof RecentRunProtocolCard
>
const mockUseAllRunsQuery = useAllRunsQuery as jest.MockedFunction<
  typeof useAllRunsQuery
>

const render = (
  props: React.ComponentProps<typeof RecentRunProtocolCarousel>
) => {
  return renderWithProviders(<RecentRunProtocolCarousel {...props} />)
}

describe('RecentRunProtocolCarousel', () => {
  let props: React.ComponentProps<typeof RecentRunProtocolCarousel>

  beforeEach(() => {
    props = {
      sortedProtocols: mockSortedProtocol,
    }
    mockRecentRunProtocolCard.mockReturnValue(
      <div>mock RecentRunProtocolCard</div>
    )
    mockUseAllRunsQuery.mockReturnValue({ data: { data: [mockRun] } } as any)
  })

  it('should render RecentRunProtocolCard', () => {
    const [{ getByText }] = render(props)
    getByText('mock RecentRunProtocolCard')
  })

  // Note(kj:04/14/2023) still looking for a way to test swipe gesture in a unit test
  it.todo('test swipe gesture')
})

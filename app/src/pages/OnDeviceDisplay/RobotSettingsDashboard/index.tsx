import * as React from 'react'
import { useSelector } from 'react-redux'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import {
  Flex,
  DIRECTION_COLUMN,
  SPACING,
  ALIGN_FLEX_END,
} from '@opentrons/components'

import { TertiaryButton } from '../../../atoms/buttons'
import { getLocalRobot, getRobotApiVersion } from '../../../redux/discovery'
import { getBuildrootUpdateAvailable } from '../../../redux/buildroot'
import { getDevtoolsEnabled } from '../../../redux/config'
import { UNREACHABLE } from '../../../redux/discovery/constants'
import { Navigation } from '../../../organisms/OnDeviceDisplay/Navigation'
import { useLights } from '../../../organisms/Devices/hooks'
import { onDeviceDisplayRoutes } from '../../../App/OnDeviceDisplayApp'
import { useNetworkConnection } from '../hooks'
import { RobotSettingButton } from './RobotSettingButton'
import { RobotSettingsContent } from './RobotSettingsContent'

import type { State } from '../../../redux/types'
import type { SettingOption } from './RobotSettingButton'

export function RobotSettingsDashboard(): JSX.Element {
  const { i18n, t } = useTranslation([
    'device_settings',
    'app_settings',
    'shared',
  ])
  const localRobot = useSelector(getLocalRobot)
  const robotName = localRobot?.name != null ? localRobot.name : 'no name'
  const networkConnection = useNetworkConnection(robotName)
  const [
    currentOption,
    setCurrentOption,
  ] = React.useState<SettingOption | null>(null)
  const robotServerVersion =
    localRobot?.status != null ? getRobotApiVersion(localRobot) : null

  const robotUpdateType = useSelector((state: State) => {
    return localRobot != null && localRobot.status !== UNREACHABLE
      ? getBuildrootUpdateAvailable(state, localRobot)
      : null
  })
  const isUpdateAvailable = robotUpdateType === 'upgrade'
  const devToolsOn = useSelector(getDevtoolsEnabled)
  const { lightsOn, toggleLights } = useLights()

  return (
    <Flex
      flexDirection={DIRECTION_COLUMN}
      columnGap={SPACING.spacing8}
      paddingX={SPACING.spacing40}
    >
      {currentOption != null ? (
        <Flex flexDirection={DIRECTION_COLUMN} columnGap={SPACING.spacing8}>
          <RobotSettingsContent
            currentOption={currentOption}
            setCurrentOption={setCurrentOption}
            networkConnection={networkConnection}
            robotName={robotName}
            robotServerVersion={
              robotServerVersion ??
              i18n.format(t('shared:unknown'), 'capitalize')
            }
            isUpdateAvailable={isUpdateAvailable}
            devToolsOn={devToolsOn}
          />
        </Flex>
      ) : (
        <Flex flexDirection={DIRECTION_COLUMN}>
          <Navigation routes={onDeviceDisplayRoutes} />
          <RobotSettingButton
            settingName={t('network_settings')}
            settingInfo={networkConnection?.connectionStatus}
            currentOption="NetworkSettings"
            setCurrentOption={setCurrentOption}
            iconName="wifi"
          />
          <Link to="/robot-settings/rename-robot">
            <RobotSettingButton
              settingName={t('robot_name')}
              settingInfo={robotName}
              currentOption="RobotName"
              setCurrentOption={setCurrentOption}
              iconName="flex-robot"
            />
          </Link>
          <RobotSettingButton
            settingName={t('robot_system_version')}
            settingInfo={
              robotServerVersion != null
                ? `v${robotServerVersion}`
                : t('robot_settings_advanced_unknown')
            }
            currentOption="RobotSystemVersion"
            setCurrentOption={setCurrentOption}
            isUpdateAvailable={isUpdateAvailable}
            iconName="update"
          />
          <RobotSettingButton
            settingName={t('display_led_lights')}
            settingInfo={t('display_led_lights_description')}
            setCurrentOption={setCurrentOption}
            iconName="light"
            ledLights
            lightsOn={Boolean(lightsOn)}
            toggleLights={toggleLights}
          />
          <RobotSettingButton
            settingName={t('touchscreen_sleep')}
            currentOption="TouchscreenSleep"
            setCurrentOption={setCurrentOption}
            iconName="sleep"
          />
          <RobotSettingButton
            settingName={t('touchscreen_brightness')}
            currentOption="TouchscreenBrightness"
            setCurrentOption={setCurrentOption}
            iconName="brightness"
          />
          <RobotSettingButton
            settingName={t('text_size')}
            currentOption="TextSize"
            setCurrentOption={setCurrentOption}
            iconName="text-size"
          />
          <RobotSettingButton
            settingName={t('device_reset')}
            currentOption="DeviceReset"
            setCurrentOption={setCurrentOption}
            iconName="reset"
          />
          <RobotSettingButton
            settingName={t('app_settings:update_channel')}
            currentOption="UpdateChannel"
            setCurrentOption={setCurrentOption}
            iconName="update-channel"
          />
          <RobotSettingButton
            settingName={t('app_settings:enable_dev_tools')}
            settingInfo={t('dev_tools_description')}
            iconName="build"
            enabledDevTools
            devToolsOn={devToolsOn}
          />
        </Flex>
      )}
      <Flex
        alignSelf={ALIGN_FLEX_END}
        padding={SPACING.spacing40}
        width="fit-content"
      >
        <Link to="menu">
          <TertiaryButton>To ODD Menu</TertiaryButton>
        </Link>
      </Flex>
    </Flex>
  )
}

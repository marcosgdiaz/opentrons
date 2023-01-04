from __future__ import annotations

import logging
from typing import List, Optional, cast

from opentrons_shared_data.labware.dev_types import LabwareDefinition

from opentrons.broker import Broker
from opentrons.hardware_control.modules import ModuleModel, ThermocyclerStep
from opentrons.commands import module_commands as cmds
from opentrons.commands.publisher import CommandPublisher, publish
from opentrons.protocols.api_support.types import APIVersion
from opentrons.protocols.api_support.util import APIVersionError, requires_version

from .core.common import (
    ProtocolCore,
    ModuleCore,
    TemperatureModuleCore,
    MagneticModuleCore,
    ThermocyclerCore,
    HeaterShakerCore,
)
from .core.core_map import LoadedCoreMap
from .core.protocol_api.legacy_module_core import LegacyModuleCore
from .core.protocol_api.module_geometry import ModuleGeometry as LegacyModuleGeometry
from .core.protocol_api.labware import LabwareImplementation as LegacyLabwareCore

from .module_validation_and_errors import (
    validate_heater_shaker_temperature,
    validate_heater_shaker_speed,
)
from .labware import Labware
from . import validation


ENGAGE_HEIGHT_UNIT_CNV = 2


_log = logging.getLogger(__name__)


class ModuleContext(CommandPublisher):
    """A connected module in the protocol.

    .. versionadded:: 2.0
    """

    def __init__(
        self,
        core: ModuleCore,
        protocol_core: ProtocolCore,
        core_map: LoadedCoreMap,
        api_version: APIVersion,
        broker: Broker,
    ) -> None:
        super().__init__(broker=broker)
        self._core = core
        self._protocol_core = protocol_core
        self._core_map = core_map
        self._api_version = api_version

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def api_version(self) -> APIVersion:
        return self._api_version

    @requires_version(2, 0)
    def load_labware_object(self, labware: Labware) -> Labware:
        """Specify the presence of a piece of labware on the module.

        :param labware: The labware object. This object should be already
                        initialized and its parent should be set to this
                        module's geometry. To initialize and load a labware
                        onto the module in one step, see
                        :py:meth:`load_labware`.
        :returns: The properly-linked labware object

        .. deprecated:: 2.14
            Use :py:meth:`load_labware` or :py:meth:`load_labware_by_definition`.
        """
        deprecation_message = (
            "`ModuleContext.load_labware_object` is an internal, deprecated method."
            " Use `ModuleContext.load_labware` or `load_labware_by_definition` instead."
        )

        if not isinstance(self._core, LegacyModuleCore):
            raise APIVersionError(deprecation_message)

        _log.warning(deprecation_message)

        assert (
            labware.parent == self._core.geometry
        ), "Labware is not configured with this module as its parent"

        return self._core.geometry.add_labware(labware)

    def load_labware(
        self,
        name: str,
        label: Optional[str] = None,
        namespace: Optional[str] = None,
        version: int = 1,
    ) -> Labware:
        """Load a labware onto the module using its load parameters.

        :param name: The name of the labware object.
        :param str label: An optional display name to give the labware.
                          If specified, this is the name the labware will use
                          in the run log and the calibration view in the Opentrons App.
        :param str namespace: The namespace the labware definition belongs to.
                              If unspecified, will search 'opentrons' then 'custom_beta'
        :param int version: The version of the labware definition.
                            If unspecified, will use version 1.

        :returns: The initialized and loaded labware object.

        .. versionadded:: 2.1
            The *label,* *namespace,* and *version* parameters.
        """
        if self._api_version < APIVersion(2, 1) and (
            label is not None or namespace is not None or version != 1
        ):
            _log.warning(
                f"You have specified API {self.api_version}, but you "
                "are trying to utilize new load_labware parameters in 2.1"
            )

        labware_core = self._protocol_core.load_labware(
            load_name=name,
            label=label,
            namespace=namespace,
            version=version,
            location=self._core,
        )

        if isinstance(self._core, LegacyModuleCore):
            labware = self._core.add_labware_core(cast(LegacyLabwareCore, labware_core))
        else:
            labware = Labware(
                implementation=labware_core,
                api_version=self._api_version,
            )

        self._core_map.add(labware_core, labware)

        return labware

    @requires_version(2, 0)
    def load_labware_from_definition(
        self, definition: LabwareDefinition, label: Optional[str] = None
    ) -> Labware:
        """Load a labware onto the module using an inline definition.

        :param definition: The labware definition.
        :param str label: An optional special name to give the labware. If
                          specified, this is the name the labware will appear
                          as in the run log and the calibration view in the
                          Opentrons app.
        :returns: The initialized and loaded labware object.
        """
        load_params = self._protocol_core.add_labware_definition(definition)

        return self.load_labware(
            name=load_params.load_name,
            namespace=load_params.namespace,
            version=load_params.version,
            label=label,
        )

    @requires_version(2, 1)
    def load_labware_by_name(
        self,
        name: str,
        label: Optional[str] = None,
        namespace: Optional[str] = None,
        version: int = 1,
    ) -> Labware:
        """
        .. deprecated:: 2.0
            Use :py:meth:`load_labware` instead.
        """
        _log.warning("load_labware_by_name is deprecated. Use load_labware instead.")
        return self.load_labware(
            name=name, label=label, namespace=namespace, version=version
        )

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def labware(self) -> Optional[Labware]:
        """The labware (if any) present on this module."""
        labware_core = self._protocol_core.get_labware_on_module(self._core)
        return self._core_map.get(labware_core)

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def geometry(self) -> LegacyModuleGeometry:
        """The object representing the module as an item on the deck.

        .. deprecated:: 2.14
            Use properties of the :py:class:`ModuleContext` instead,
            like :py:meth:`model` and :py:meth:`type`
        """
        if isinstance(self._core, LegacyModuleCore):
            return self._core.geometry

        raise APIVersionError(
            "`ModuleContext.geometry` has been deprecated;"
            " use properties of the `ModuleContext` itself, instead."
        )

    @property
    def requested_as(self) -> ModuleModel:
        """How the protocol requested this module.

        For example, a physical ``temperatureModuleV2`` might have been requested
        either as ``temperatureModuleV2`` or ``temperatureModuleV1``.

        For Opentrons internal use only.

        :meta private:
        """
        return self._core.get_requested_model()

    def __repr__(self) -> str:
        return "{} at {} lw {}".format(
            self.__class__.__name__, self.geometry, self.labware
        )


class TemperatureModuleContext(ModuleContext):
    """An object representing a connected Temperature Module.

    It should not be instantiated directly; instead, it should be
    created through :py:meth:`.ProtocolContext.load_module`.

    .. versionadded:: 2.0

    """

    _core: TemperatureModuleCore

    @publish(command=cmds.tempdeck_set_temp)
    @requires_version(2, 0)
    def set_temperature(self, celsius: float) -> None:
        """Set a target temperature and wait until the module reaches the target.

        No other protocol commands will execute while waiting for the temperature.

        :param celsius: A value between 4 and 95, representing the target temperature in °C.
        """
        self._core.set_target_temperature(celsius)
        self._core.wait_for_target_temperature()

    @publish(command=cmds.tempdeck_set_temp)
    @requires_version(2, 3)
    def start_set_temperature(self, celsius: float) -> None:
        """Set the target temperature without waiting for the target to be hit.

        :param celsius: A value between 4 and 95, representing the target temperature in °C.
        """
        self._core.set_target_temperature(celsius)

    @publish(command=cmds.tempdeck_await_temp)
    @requires_version(2, 3)
    def await_temperature(self, celsius: float) -> None:
        """Wait until module reaches temperature.

        :param celsius: A value between 4 and 95, representing the target temperature in °C.
        """
        self._core.wait_for_target_temperature(celsius)

    @publish(command=cmds.tempdeck_deactivate)
    @requires_version(2, 0)
    def deactivate(self) -> None:
        """Stop heating or cooling, and turn off the fan."""
        self._core.deactivate()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def temperature(self) -> float:
        """The current temperature of the Temperature Module's deck in °C.

        Returns ``0`` in simulation if no target temperature has been set.
        """
        return self._core.get_current_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def target(self) -> Optional[float]:
        """The target temperature of the Temperature Module's deck in °C.

        Returns ``None`` if no target has been set.
        """
        return self._core.get_target_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 3)
    def status(self) -> str:
        """One of four possible temperature statuses:

        - ``holding at target`` – The module has reached its target temperature
          and is actively maintaining that temperature.
        - ``cooling`` – The module is cooling to a target temperature.
        - ``heating`` – The module is heating to a target temperature.
        - ``idle`` – The module has been deactivated.
        """
        return self._core.get_status().value


class MagneticModuleContext(ModuleContext):
    """An object representing a connected Magnetic Module.

    It should not be instantiated directly; instead, it should be
    created through :py:meth:`.ProtocolContext.load_module`.

    .. versionadded:: 2.0
    """

    _core: MagneticModuleCore

    @publish(command=cmds.magdeck_calibrate)
    @requires_version(2, 0)
    def calibrate(self) -> None:
        """Calibrate the Magnetic Module.

        .. deprecated:: 2.14
            This method is unnecessary; remove any usage.
        """
        _log.warning(
            "`MagneticModuleContext.calibrate` doesn't do anything useful"
            " and will no-op in Protocol API version 2.14 and higher."
        )
        if self._api_version < APIVersion(2, 14):
            self._core._sync_module_hardware.calibrate()  # type: ignore[attr-defined]

    @publish(command=cmds.magdeck_engage)
    @requires_version(2, 0)
    def engage(
        self,
        height: Optional[float] = None,
        offset: Optional[float] = None,
        height_from_base: Optional[float] = None,
    ) -> None:
        """Raise the Magnetic Module's magnets.  You can specify how high the magnets
        should move:

           - No parameter: Move to the default height for the loaded labware. If
             the loaded labware has no default, or if no labware is loaded, this will
             raise an error.

           - ``height_from_base`` – Move this many millimeters above the bottom
             of the labware. Acceptable values are between ``0`` and ``25``.

             This is the recommended way to adjust the magnets' height.

           - ``offset`` – Move this many millimeters above (positive value) or below
             (negative value) the default height for the loaded labware. The sum of
             the default height and ``offset`` must be between 0 and 25.

           - ``height`` – Intended to move this many millimeters above the magnets'
             home position. However, depending on the generation of module and the loaded
             labware, this may produce unpredictable results. You should normally use
             ``height_from_base`` instead.

             This parameter may be deprecated in a future release of the Python API.

        You shouldn't specify more than one of these parameters. However, if you do,
        their order of precedence is ``height``, then ``height_from_base``, then ``offset``.

        .. versionadded:: 2.2
            The *height_from_base* parameter.
        """
        if height is not None:
            self._core.engage(height_from_home=height)

        # This version check has a bug:
        # if the caller sets height_from_base in an API version that's too low,
        # we will silently ignore it instead of raising APIVersionError.
        # Leaving this unfixed because we haven't thought through
        # how to do backwards-compatible fixes to our version checking itself.
        elif height_from_base is not None and self._api_version >= APIVersion(2, 2):
            self._core.engage(height_from_base=height_from_base)

        else:
            self._core.engage_to_labware(
                offset=offset or 0,
                preserve_half_mm=self._api_version < APIVersion(2, 3),
            )

    @publish(command=cmds.magdeck_disengage)
    @requires_version(2, 0)
    def disengage(self) -> None:
        """Lower the magnets back into the Magnetic Module."""
        self._core.disengage()

    @property  # type: ignore
    @requires_version(2, 0)
    def status(self) -> str:
        """The status of the module, either ``engaged`` or ``disengaged``."""
        return self._core.get_status().value


class ThermocyclerContext(ModuleContext):
    """An object representing a connected Thermocycler Module.

    It should not be instantiated directly; instead, it should be
    created through :py:meth:`.ProtocolContext.load_module`.

    .. versionadded:: 2.0
    """

    _core: ThermocyclerCore

    @publish(command=cmds.thermocycler_open)
    @requires_version(2, 0)
    def open_lid(self) -> str:
        """Open the lid."""
        return self._core.open_lid().value

    @publish(command=cmds.thermocycler_close)
    @requires_version(2, 0)
    def close_lid(self) -> str:
        """Close the lid."""
        return self._core.close_lid().value

    @publish(command=cmds.thermocycler_set_block_temp)
    @requires_version(2, 0)
    def set_block_temperature(
        self,
        temperature: float,
        hold_time_seconds: Optional[float] = None,
        hold_time_minutes: Optional[float] = None,
        ramp_rate: Optional[float] = None,
        block_max_volume: Optional[float] = None,
    ) -> None:
        """Set the target temperature for the well block, in °C.

        :param temperature: A value between 4 and 99, representing the target
                            temperature in °C.
        :param hold_time_minutes: The number of minutes to hold, after reaching
                                  ``temperature``, before proceeding to the
                                  next command. If ``hold_time_seconds`` is also
                                  specified, the times are added together.
        :param hold_time_seconds: The number of seconds to hold, after reaching
                                  ``temperature``, before proceeding to the
                                  next command. If ``hold_time_minutes`` is also
                                  specified, the times are added together.
        :param block_max_volume: The greatest volume of liquid contained in any
                                 individual well of the loaded labware, in µL.
                                 If not specified, the default is 25 µL.

        .. note:

            If ``hold_time_minutes`` and ``hold_time_seconds`` are not
            specified, the Thermocycler will proceed to the next command
            immediately after ``temperature`` is reached.
        """
        seconds = validation.ensure_hold_time_seconds(
            seconds=hold_time_seconds, minutes=hold_time_minutes
        )
        self._core.set_target_block_temperature(
            celsius=temperature,
            hold_time_seconds=seconds,
            block_max_volume=block_max_volume,
        )
        self._core.wait_for_block_temperature()

    @publish(command=cmds.thermocycler_set_lid_temperature)
    @requires_version(2, 0)
    def set_lid_temperature(self, temperature: float) -> None:
        """Set the target temperature for the heated lid, in °C.

        :param temperature: A value between 37 and 110, representing the target
                            temperature in °C.

        .. note:

            The Thermocycler will proceed to the next command immediately after
            ``temperature`` has been reached.

        """
        self._core.set_target_lid_temperature(celsius=temperature)
        self._core.wait_for_lid_temperature()

    @publish(command=cmds.thermocycler_execute_profile)
    @requires_version(2, 0)
    def execute_profile(
        self,
        steps: List[ThermocyclerStep],
        repetitions: int,
        block_max_volume: Optional[float] = None,
    ) -> None:
        """Execute a Thermocycler profile, defined as a cycle of
        ``steps``, for a given number of ``repetitions``.

        :param steps: List of unique steps that make up a single cycle.
                      Each list item should be a dictionary that maps to
                      the parameters of the :py:meth:`set_block_temperature`
                      method with a ``temperature`` key, and either or both of
                      ``hold_time_seconds`` and ``hold_time_minutes``.
        :param repetitions: The number of times to repeat the cycled steps.
        :param block_max_volume: The greatest volume of liquid contained in any
                                 individual well of the loaded labware, in µL.
                                 If not specified, the default is 25 µL.

        .. note:

            Unlike with :py:meth:`set_block_temperature`, either or both of
            ``hold_time_minutes`` and ``hold_time_seconds`` must be defined
            and for each step.

        """
        repetitions = validation.ensure_thermocycler_repetition_count(repetitions)
        validated_steps = validation.ensure_thermocycler_profile_steps(steps)
        self._core.execute_profile(
            steps=validated_steps,
            repetitions=repetitions,
            block_max_volume=block_max_volume,
        )

    @publish(command=cmds.thermocycler_deactivate_lid)
    @requires_version(2, 0)
    def deactivate_lid(self) -> None:
        """Turn off the lid heater."""
        self._core.deactivate_lid()

    @publish(command=cmds.thermocycler_deactivate_block)
    @requires_version(2, 0)
    def deactivate_block(self) -> None:
        """Turn off the well block temperature controller."""
        self._core.deactivate_block()

    @publish(command=cmds.thermocycler_deactivate)
    @requires_version(2, 0)
    def deactivate(self) -> None:
        """Turn off both the well block temperature controller and the lid heater."""
        self._core.deactivate()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def lid_position(self) -> Optional[str]:
        """One of these possible lid statuses:

        - ``closed`` – The lid is closed.
        - ``in_between`` – The lid is neither open nor closed.
        - ``open`` – The lid is open.
        - ``unknown`` – The lid position can't be determined.
        """
        status = self._core.get_lid_position()
        return status.value if status is not None else None

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def block_temperature_status(self) -> str:
        """One of five possible temperature statuses:

        - ``holding at target`` – The block has reached its target temperature
          and is actively maintaining that temperature.
        - ``cooling`` – The block is cooling to a target temperature.
        - ``heating`` – The block is heating to a target temperature.
        - ``idle`` – The block is not currently heating or cooling.
        - ``error`` – The temperature status can't be determined.
        """
        return self._core.get_block_temperature_status().value

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def lid_temperature_status(self) -> Optional[str]:
        """One of five possible temperature statuses:

        - ``holding at target`` – The lid has reached its target temperature
          and is actively maintaining that temperature.
        - ``cooling`` – The lid has previously heated and is now passively cooling.
            `The Thermocycler lid does not have active cooling.`
        - ``heating`` – The lid is heating to a target temperature.
        - ``idle`` – The lid has not heated since the beginning of the protocol.
        - ``error`` – The temperature status can't be determined.
        """
        status = self._core.get_lid_temperature_status()
        return status.value if status is not None else None

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def block_temperature(self) -> Optional[float]:
        """The current temperature of the well block in °C."""
        return self._core.get_block_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def block_target_temperature(self) -> Optional[float]:
        """The target temperature of the well block in °C."""
        return self._core.get_block_target_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def lid_temperature(self) -> Optional[float]:
        """The current temperature of the lid in °C."""
        return self._core.get_lid_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def lid_target_temperature(self) -> Optional[float]:
        """The target temperature of the lid in °C."""
        return self._core.get_lid_target_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def ramp_rate(self) -> Optional[float]:
        """The current ramp rate in °C/s."""
        return self._core.get_ramp_rate()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def hold_time(self) -> Optional[float]:
        """Remaining hold time in seconds."""
        return self._core.get_hold_time()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def total_cycle_count(self) -> Optional[int]:
        """Number of repetitions for current set cycle"""
        return self._core.get_total_cycle_count()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def current_cycle_index(self) -> Optional[int]:
        """Index of the current set cycle repetition"""
        return self._core.get_current_cycle_index()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def total_step_count(self) -> Optional[int]:
        """Number of steps within the current cycle"""
        return self._core.get_total_step_count()

    @property  # type: ignore[misc]
    @requires_version(2, 0)
    def current_step_index(self) -> Optional[int]:
        """Index of the current step within the current cycle"""
        return self._core.get_current_step_index()


class HeaterShakerContext(ModuleContext):
    """An object representing a connected Heater-Shaker Module.

    It should not be instantiated directly; instead, it should be
    created through :py:meth:`.ProtocolContext.load_module`.

    .. versionadded:: 2.13
    """

    _core: HeaterShakerCore

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def target_temperature(self) -> Optional[float]:
        """The target temperature of the Heater-Shaker's plate in °C.

        Returns ``None`` if no target has been set.
        """
        return self._core.get_target_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def current_temperature(self) -> float:
        """The current temperature of the Heater-Shaker's plate in °C.

        Returns ``23`` in simulation if no target temperature has been set.
        """
        return self._core.get_current_temperature()

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def current_speed(self) -> int:
        """The current speed of the Heater-Shaker's plate in rpm."""
        return self._core.get_current_speed()

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def target_speed(self) -> Optional[int]:
        """Target speed of the Heater-Shaker's plate in rpm."""
        return self._core.get_target_speed()

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def temperature_status(self) -> str:
        """One of five possible temperature statuses:

        - ``holding at target`` – The module has reached its target temperature
          and is actively maintaining that temperature.
        - ``cooling`` – The module has previously heated and is now passively cooling.
          `The Heater-Shaker does not have active cooling.`
        - ``heating`` – The module is heating to a target temperature.
        - ``idle`` – The module has not heated since the beginning of the protocol.
        - ``error`` – The temperature status can't be determined.
        """
        return self._core.get_temperature_status().value

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def speed_status(self) -> str:
        """One of five possible shaking statuses:

        - ``holding at target`` – The module has reached its target shake speed
          and is actively maintaining that speed.
        - ``speeding up`` – The module is increasing its shake speed towards a target.
        - ``slowing down`` – The module was previously shaking at a faster speed
          and is currently reducing its speed to a lower target or to deactivate.
        - ``idle`` – The module is not shaking.
        - ``error`` – The shaking status can't be determined.
        """
        return self._core.get_speed_status().value

    @property  # type: ignore[misc]
    @requires_version(2, 13)
    def labware_latch_status(self) -> str:
        """One of six possible latch statuses:

        - ``opening`` – The latch is currently opening (in motion).
        - ``idle_open`` – The latch is open and not moving.
        - ``closing`` – The latch is currently closing (in motion).
        - ``idle_closed`` – The latch is closed and not moving.
        - ``idle_unknown`` – The default status upon reset, regardless of physical latch position.
          Use :py:meth:`~HeaterShakerContext.close_labware_latch` before other commands
          requiring confirmation that the latch is closed.
        - ``unknown`` – The latch status can't be determined.
        """
        return self._core.get_labware_latch_status().value

    @requires_version(2, 13)
    def set_and_wait_for_temperature(self, celsius: float) -> None:
        """Set a target temperature and wait until the module reaches the target.

        No other protocol commands will execute while waiting for the temperature.

        :param celsius: A value between 27 and 95, representing the target temperature in °C.
                        Values are automatically truncated to two decimal places,
                        and the Heater-Shaker module has a temperature accuracy of ±0.5 °C.
        """
        self.set_target_temperature(celsius=celsius)
        self.wait_for_temperature()

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_set_target_temperature)
    def set_target_temperature(self, celsius: float) -> None:
        """Set target temperature and return immediately.

        Sets the Heater-Shaker's target temperature and returns immediately without
        waiting for the target to be reached. Does not delay the protocol until
        target temperature has reached.
        Use :py:meth:`~.HeaterShakerContext.wait_for_temperature` to delay
        protocol execution.

        :param celsius: A value between 27 and 95, representing the target temperature in °C.
                        Values are automatically truncated to two decimal places,
                        and the Heater-Shaker module has a temperature accuracy of ±0.5 °C.
        """
        validated_temp = validate_heater_shaker_temperature(celsius=celsius)
        self._core.set_target_temperature(celsius=validated_temp)

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_wait_for_temperature)
    def wait_for_temperature(self) -> None:
        """Delays protocol execution until the Heater-Shaker has reached its target
        temperature.

        Raises an error if no target temperature was previously set.
        """
        self._core.wait_for_target_temperature()

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_set_and_wait_for_shake_speed)
    def set_and_wait_for_shake_speed(self, rpm: int) -> None:
        """Set a shake speed in rpm and block execution of further commands until the module reaches the target.

        Reaching a target shake speed typically only takes a few seconds.

        .. note::

            Before shaking, this command will retract the pipettes upward if they are parked adjacent to the Heater-Shaker.

        :param rpm: A value between 200 and 3000, representing the target shake speed in revolutions per minute.
        """
        validated_speed = validate_heater_shaker_speed(rpm=rpm)
        self._core.set_and_wait_for_shake_speed(rpm=validated_speed)

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_open_labware_latch)
    def open_labware_latch(self) -> None:
        """Open the Heater-Shaker's labware latch.

        The labware latch needs to be closed before:
            * Shaking
            * Pipetting to or from the labware on the Heater-Shaker
            * Pipetting to or from labware to the left or right of the Heater-Shaker

        Attempting to open the latch while the Heater-Shaker is shaking will raise an error.

        .. note::

            Before opening the latch, this command will retract the pipettes upward
            if they are parked adjacent to the left or right of the Heater-Shaker.
        """
        self._core.open_labware_latch()

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_close_labware_latch)
    def close_labware_latch(self) -> None:
        """Closes the labware latch.

        The labware latch needs to be closed using this method before sending a shake command,
        even if the latch was manually closed before starting the protocol.
        """
        self._core.close_labware_latch()

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_deactivate_shaker)
    def deactivate_shaker(self) -> None:
        """Stops shaking.

        Decelerating to 0 rpm typically only takes a few seconds.
        """
        self._core.deactivate_shaker()

    @requires_version(2, 13)
    @publish(command=cmds.heater_shaker_deactivate_heater)
    def deactivate_heater(self) -> None:
        """Stops heating.

        The module will passively cool to room temperature.
        The Heater-Shaker does not have active cooling.
        """
        self._core.deactivate_heater()

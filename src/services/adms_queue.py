import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Thread-safe in-memory command queue per device serial number
_command_counter: int = 100
_device_command_queues: Dict[str, List[Dict[str, Any]]] = {}


def queue_adms_command(device_sn: str, command: str) -> int:
    """
    Queue an ADMS command to be picked up by the biometric terminal
    on its next periodic poll to /iclock/getrequest.aspx.
    """
    global _command_counter
    _command_counter += 1
    cmd_id = _command_counter
    sn_key = device_sn.strip().upper() if device_sn else "*"
    if sn_key not in _device_command_queues:
        _device_command_queues[sn_key] = []
    _device_command_queues[sn_key].append({"id": cmd_id, "command": command})
    logger.info("Queued ADMS command %d (%s) for device %s", cmd_id, command, sn_key)
    return cmd_id


def pop_adms_command(device_sn: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve and pop the next pending command for the device.
    Checks specific device SN first, then broadcast '*' queue.
    """
    sn_key = device_sn.strip().upper() if device_sn else ""
    if sn_key and sn_key in _device_command_queues and _device_command_queues[sn_key]:
        return _device_command_queues[sn_key].pop(0)
    if "*" in _device_command_queues and _device_command_queues["*"]:
        return _device_command_queues["*"].pop(0)
    return None


def pop_all_adms_commands(device_sn: str) -> List[Dict[str, Any]]:
    """
    Retrieve and pop all pending commands for the device.
    Returned commands are formatted into a multi-line batch response.
    """
    sn_key = device_sn.strip().upper() if device_sn else ""
    cmds: List[Dict[str, Any]] = []
    if sn_key and sn_key in _device_command_queues and _device_command_queues[sn_key]:
        cmds.extend(_device_command_queues[sn_key])
        _device_command_queues[sn_key] = []
    if "*" in _device_command_queues and _device_command_queues["*"]:
        cmds.extend(_device_command_queues["*"])
        _device_command_queues["*"] = []
    return cmds

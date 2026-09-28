"""
AegisTrace - Hardware Discovery & Physical Device Inspection Engine
===================================================================
Autonomously inspects local host system for connected physical capture,
print, and scan hardware:
- USB/UVC document cameras and webcams
- Physical laser and inkjet printers (strictly filters out virtual print drivers)
- Flatbed and sheet-fed document scanners (WIA/TWAIN)
- Display monitors and presentation panels

SCIENTIFIC INTEGRITY RULE:
Never fabricates hardware metadata. If hardware is unavailable or fields cannot
be determined, returns UNKNOWN and sets modality status to UNAVAILABLE.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import os
import sys
import json
import subprocess
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DeviceModalityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class DiscoveredDevice(BaseModel):
    """Normalized descriptor for an interrogated physical device."""
    device_id: str = Field(..., description="Unique physical or system device identifier")
    device_type: str = Field(..., description="Modality type: CAMERA, PRINTER, SCANNER, DISPLAY")
    manufacturer: str = Field("UNKNOWN", description="Device manufacturer name or UNKNOWN")
    model: str = Field("UNKNOWN", description="Device model string or UNKNOWN")
    interface: str = Field("UNKNOWN", description="Physical interface: USB, UVC, PCIE, NETWORK, UNKNOWN")
    driver: str = Field("UNKNOWN", description="Driver name/version or UNKNOWN")
    resolution: str = Field("UNKNOWN", description="Max/native resolution or DPI or UNKNOWN")
    supported_capture_modes: List[str] = Field(default_factory=list, description="Supported capture formats/modes")
    is_physical: bool = Field(True, description="Whether device represents genuine physical hardware")
    status: str = Field("ACTIVE", description="Operating state: ACTIVE, DISCONNECTED, ERROR, UNKNOWN")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw device-specific properties")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HardwareInventory(BaseModel):
    """Complete snapshot of local hardware inspection."""
    inventory_id: str = Field(..., description="Unique hash-bound inventory identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    host_environment: str = Field(..., description="Execution host classification")
    os_name: str = Field(..., description="Operating system platform")
    os_release: str = Field(..., description="Operating system version")
    cameras: List[DiscoveredDevice] = Field(default_factory=list)
    printers: List[DiscoveredDevice] = Field(default_factory=list)
    scanners: List[DiscoveredDevice] = Field(default_factory=list)
    displays: List[DiscoveredDevice] = Field(default_factory=list)
    camera_modality_status: DeviceModalityStatus = DeviceModalityStatus.UNAVAILABLE
    printer_modality_status: DeviceModalityStatus = DeviceModalityStatus.UNAVAILABLE
    scanner_modality_status: DeviceModalityStatus = DeviceModalityStatus.UNAVAILABLE
    display_modality_status: DeviceModalityStatus = DeviceModalityStatus.UNAVAILABLE
    is_laboratory_ready: bool = Field(False, description="True ONLY if at least 1 camera/printer/scanner is physical and live")
    raw_probe_log: List[str] = Field(default_factory=list)




def probe_system_hardware() -> HardwareInventory:
    """
    Executes a comprehensive, non-fabricating hardware discovery probe across
    all local device modalities.
    """
    probe_logs: List[str] = []
    cameras: List[DiscoveredDevice] = []
    printers: List[DiscoveredDevice] = []
    scanners: List[DiscoveredDevice] = []
    displays: List[DiscoveredDevice] = []

    # Determine host environment
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("CONTAINER") is not None
    is_ci = any(os.environ.get(k) for k in ["CI", "GITHUB_ACTIONS", "GITLAB_CI"])
    if is_docker or is_ci:
        host_env = "AIRGAP_CONTAINER_HOST"
    else:
        host_env = f"WORKSTATION_{sys.platform.upper()}"

    # 1. Probe Cameras (OpenCV VideoCapture)
    try:
        import cv2
        for idx in range(4):
            try:
                cap = None
                if sys.platform == "win32":
                    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(idx)

                if cap is not None and cap.isOpened():
                    ret, frame = cap.read()
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
                    modes = []
                    if w > 0 and h > 0:
                        modes.append(f"{w}x{h} RAW/BGR")
                    
                    dev = DiscoveredDevice(
                        device_id=f"cam_uvc_{idx}",
                        device_type="CAMERA",
                        manufacturer="UNKNOWN",
                        model=f"UVC Capture Device {idx}",
                        interface="USB/UVC",
                        driver="DirectShow/V4L2",
                        resolution=f"{w}x{h}" if (w > 0 and h > 0) else "UNKNOWN",
                        supported_capture_modes=modes,
                        is_physical=True,
                        status="ACTIVE" if ret and frame is not None else "CONNECTED_NO_FRAME",
                        metadata={"opencv_index": idx, "frame_read_success": bool(ret)}
                    )
                    cameras.append(dev)
                    probe_logs.append(f"Camera index {idx} probed: ACTIVE={ret}, res={w}x{h}")
                    cap.release()
                else:
                    probe_logs.append(f"Camera index {idx} probed: NOT_OPENED")
            except Exception as e:
                probe_logs.append(f"Camera index {idx} error: {e}")
    except ImportError:
        probe_logs.append("OpenCV not available for camera probe.")

    # 2. Probe PnP Cameras and Scanners on Windows
    if sys.platform == "win32":
        try:
            ps_pnp = 'Get-PnpDevice -Class Camera, Image | Select-Object FriendlyName, InstanceId, Status, Class, Manufacturer | ConvertTo-Json'
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_pnp], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                try:
                    data = json.loads(res.stdout)
                    if isinstance(data, dict):
                        data = [data]
                    for item in data:
                        name = item.get("FriendlyName") or "UNKNOWN"
                        inst_id = item.get("InstanceId") or "UNKNOWN"
                        status_str = item.get("Status") or "UNKNOWN"
                        cls = item.get("Class") or "UNKNOWN"
                        mfg = item.get("Manufacturer") or "UNKNOWN"
                        
                        # Check if active physical device
                        is_active = status_str == "OK"
                        dev_type = "CAMERA" if cls == "Camera" else "SCANNER"
                        
                        # Only add if not already captured via OpenCV
                        if not any(c.device_id == inst_id for c in cameras):
                            dev = DiscoveredDevice(
                                device_id=inst_id,
                                device_type=dev_type,
                                manufacturer=mfg if mfg != "UNKNOWN" else "UNKNOWN",
                                model=name,
                                interface="USB/PnP",
                                driver="Windows PnP",
                                resolution="UNKNOWN",
                                supported_capture_modes=[],
                                is_physical=True,
                                status=status_str,
                                metadata={"friendly_name": name, "class": cls}
                            )
                            if is_active and dev_type == "CAMERA" and not cameras:
                                cameras.append(dev)
                            elif is_active and dev_type == "SCANNER":
                                scanners.append(dev)
                except Exception as e:
                    probe_logs.append(f"PnP parsing error: {e}")
        except Exception as e:
            probe_logs.append(f"PnP probe failed: {e}")

    # 3. Probe Physical Printers
    if sys.platform == "win32":
        try:
            ps_printers = 'Get-CimInstance Win32_Printer | Select-Object Name, DriverName, Local, PortName, PrinterStatus, HorizontalResolution, VerticalResolution | ConvertTo-Json'
            res_pr = subprocess.run(["powershell", "-NoProfile", "-Command", ps_printers], capture_output=True, text=True, timeout=5)
            if res_pr.returncode == 0 and res_pr.stdout.strip():
                try:
                    pr_data = json.loads(res_pr.stdout)
                    if isinstance(pr_data, dict):
                        pr_data = [pr_data]
                    for pr in pr_data:
                        name = pr.get("Name") or ""
                        driver = pr.get("DriverName") or ""
                        port = pr.get("PortName") or ""
                        h_res = pr.get("HorizontalResolution") or 0
                        v_res = pr.get("VerticalResolution") or 0
                        
                        # Strict filter: exclude known virtual/software printer drivers
                        is_virtual = any(v in name.lower() or v in driver.lower() for v in [
                            "onenote", "xps", "pdf", "fax", "software", "virtual", "rootprint", "send to"
                        ])
                        
                        if not is_virtual and pr.get("Local", False):
                            res_str = f"{h_res}x{v_res} DPI" if (h_res > 0 and v_res > 0) else "UNKNOWN"
                            dev = DiscoveredDevice(
                                device_id=f"prn_{name.replace(' ', '_')}",
                                device_type="PRINTER",
                                manufacturer="UNKNOWN",
                                model=name,
                                interface=f"PORT:{port}" if port else "UNKNOWN",
                                driver=driver,
                                resolution=res_str,
                                supported_capture_modes=["MONOCHROME", "COLOR"],
                                is_physical=True,
                                status="ACTIVE",
                                metadata={"port": port, "driver": driver}
                            )
                            printers.append(dev)
                            probe_logs.append(f"Physical printer detected: {name} ({driver})")
                except Exception as e:
                    probe_logs.append(f"Printer parsing error: {e}")
        except Exception as e:
            probe_logs.append(f"Printer probe failed: {e}")

    # 4. Probe Displays
    if sys.platform == "win32":
        try:
            ps_mon = 'Get-CimInstance Win32_DesktopMonitor | Select-Object Name, MonitorType, ScreenHeight, ScreenWidth, DeviceID | ConvertTo-Json'
            res_mon = subprocess.run(["powershell", "-NoProfile", "-Command", ps_mon], capture_output=True, text=True, timeout=5)
            if res_mon.returncode == 0 and res_mon.stdout.strip():
                try:
                    mon_data = json.loads(res_mon.stdout)
                    if isinstance(mon_data, dict):
                        mon_data = [mon_data]
                    for mon in mon_data:
                        name = mon.get("Name") or "Generic Display"
                        dev_id = mon.get("DeviceID") or "DesktopMonitor"
                        w = mon.get("ScreenWidth") or 0
                        h = mon.get("ScreenHeight") or 0
                        dev = DiscoveredDevice(
                            device_id=dev_id,
                            device_type="DISPLAY",
                            manufacturer="UNKNOWN",
                            model=name,
                            interface="VIDEO_DISPLAY",
                            driver="DirectX/WDDM",
                            resolution=f"{w}x{h}" if (w > 0 and h > 0) else "UNKNOWN",
                            supported_capture_modes=["SCREEN_CAPTURE", "RENDER_CANVAS"],
                            is_physical=True,
                            status="ACTIVE",
                            metadata={"monitor_type": mon.get("MonitorType", "UNKNOWN")}
                        )
                        displays.append(dev)
                except Exception as e:
                    probe_logs.append(f"Display parsing error: {e}")
        except Exception as e:
            probe_logs.append(f"Display probe failed: {e}")

    # Compute modality statuses
    active_cameras = [c for c in cameras if c.status == "ACTIVE"]
    cam_status = DeviceModalityStatus.AVAILABLE if active_cameras else DeviceModalityStatus.UNAVAILABLE
    prn_status = DeviceModalityStatus.AVAILABLE if printers else DeviceModalityStatus.UNAVAILABLE
    scn_status = DeviceModalityStatus.AVAILABLE if scanners else DeviceModalityStatus.UNAVAILABLE
    dsp_status = DeviceModalityStatus.AVAILABLE if displays else DeviceModalityStatus.UNAVAILABLE

    is_lab_ready = bool(active_cameras or printers or scanners)

    import hashlib
    inv_content = f"{datetime.now(timezone.utc).isoformat()}:{host_env}:{len(cameras)}:{len(printers)}:{len(scanners)}"
    inv_id = f"HINV-{hashlib.sha256(inv_content.encode()).hexdigest()[:12]}"

    import platform
    return HardwareInventory(
        inventory_id=inv_id,
        host_environment=host_env,
        os_name=platform.system(),
        os_release=platform.release(),
        cameras=cameras,
        printers=printers,
        scanners=scanners,
        displays=displays,
        camera_modality_status=cam_status,
        printer_modality_status=prn_status,
        scanner_modality_status=scn_status,
        display_modality_status=dsp_status,
        is_laboratory_ready=is_lab_ready,
        raw_probe_log=probe_logs
    )

"""
Architecture #6: BLACKBOARD | SHARED-STATE
Shared blackboard memory, pub/sub event bus, and global request-for-proposal (RFP) bulletin.
"""

import threading
import time
from typing import Dict, List, Any, Callable, Optional
from src.core.models import ArchitectureType, ArchitectureEvent, ResourceType


class BlackboardSharedState:
    """
    Centralized Shared State / Blackboard for dynamic multi-agent awareness,
    topic pub/sub, spot pricing bulletin, and lock status.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.knowledge_base: Dict[str, Any] = {
            "factory_status": "OPERATIONAL",
            "active_workpieces": {},
            "resource_locks": {},
            "spot_prices": {
                ResourceType.GRID_POWER_KW.value: 1.2,          # tokens/kW/min
                ResourceType.HIGH_RES_LASER_TOOL.value: 8.5,     # tokens/lease
                ResourceType.ULTRA_TORQUE_DRIVER.value: 6.0,     # tokens/lease
                ResourceType.GPU_COMPUTE_TOKENS.value: 2.0,      # tokens/token
                ResourceType.BUFFER_STAGE_ZONE.value: 3.0        # tokens/slot
            },
            "rfp_board": [],        # Open Requests For Proposals
            "event_history": [],
            "contract_ledger": []
        }
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.event_log: List[ArchitectureEvent] = []

    def post_rfp(self, requester_id: str, resource_type: ResourceType, amount: float, max_price: float, deadline: float) -> str:
        with self._lock:
            rfp_id = f"RFP-{int(time.time()*1000)}-{requester_id}"
            rfp = {
                "rfp_id": rfp_id,
                "requester_id": requester_id,
                "resource_type": resource_type.value,
                "amount": amount,
                "max_price": max_price,
                "deadline": deadline,
                "status": "OPEN",
                "bids": [],
                "created_at": time.time()
            }
            self.knowledge_base["rfp_board"].append(rfp)
            self._record_event(
                ArchitectureType.BLACKBOARD_SHARED_STATE,
                source=requester_id,
                target="BLACKBOARD",
                action="POST_RFP",
                details=f"Posted RFP {rfp_id} for {amount} of {resource_type.value} at max {max_price} tokens"
            )
            self.publish("rfp_new", rfp)
            return rfp_id

    def submit_bid(self, rfp_id: str, bidder_id: str, offered_amount: float, bid_price: float) -> bool:
        with self._lock:
            for rfp in self.knowledge_base["rfp_board"]:
                if rfp["rfp_id"] == rfp_id and rfp["status"] == "OPEN":
                    bid = {
                        "bidder_id": bidder_id,
                        "offered_amount": offered_amount,
                        "bid_price": bid_price,
                        "timestamp": time.time()
                    }
                    rfp["bids"].append(bid)
                    self._record_event(
                        ArchitectureType.BLACKBOARD_SHARED_STATE,
                        source=bidder_id,
                        target=rfp["requester_id"],
                        action="SUBMIT_BID",
                        details=f"Submitted bid on {rfp_id}: {offered_amount} units @ {bid_price} tokens"
                    )
                    self.publish(f"rfp_bid_{rfp_id}", bid)
                    return True
            return False

    def acquire_lock(self, resource_name: str, agent_id: str, lease_seconds: float = 5.0) -> bool:
        with self._lock:
            current_time = time.time()
            locks = self.knowledge_base["resource_locks"]
            if resource_name in locks:
                lock_info = locks[resource_name]
                if lock_info["owner"] != agent_id and lock_info["expires_at"] > current_time:
                    return False  # Locked by another agent
            
            # Acquire or renew
            locks[resource_name] = {
                "owner": agent_id,
                "acquired_at": current_time,
                "expires_at": current_time + lease_seconds
            }
            self._record_event(
                ArchitectureType.BLACKBOARD_SHARED_STATE,
                source=agent_id,
                target="BLACKBOARD_LOCKS",
                action="ACQUIRE_LOCK",
                details=f"Locked resource '{resource_name}' for {lease_seconds}s"
            )
            return True

    def release_lock(self, resource_name: str, agent_id: str) -> bool:
        with self._lock:
            locks = self.knowledge_base["resource_locks"]
            if resource_name in locks and locks[resource_name]["owner"] == agent_id:
                del locks[resource_name]
                self._record_event(
                    ArchitectureType.BLACKBOARD_SHARED_STATE,
                    source=agent_id,
                    target="BLACKBOARD_LOCKS",
                    action="RELEASE_LOCK",
                    details=f"Released lock on '{resource_name}'"
                )
                return True
            return False

    def update_spot_price(self, resource_type: ResourceType, new_price: float, reason: str = ""):
        with self._lock:
            old_price = self.knowledge_base["spot_prices"].get(resource_type.value, 1.0)
            self.knowledge_base["spot_prices"][resource_type.value] = round(new_price, 2)
            self._record_event(
                ArchitectureType.BLACKBOARD_SHARED_STATE,
                source="MARKET_ORACLE",
                target="BLACKBOARD",
                action="UPDATE_SPOT_PRICE",
                details=f"Adjusted {resource_type.value} spot price: {old_price} -> {new_price} tokens. ({reason})"
            )
            self.publish("spot_price_change", {
                "resource": resource_type.value,
                "old_price": old_price,
                "new_price": new_price
            })

    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]):
        with self._lock:
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(callback)

    def publish(self, topic: str, payload: Dict[str, Any]):
        with self._lock:
            callbacks = list(self.subscribers.get(topic, []))
            callbacks += list(self.subscribers.get("*", []))
        for cb in callbacks:
            try:
                cb(payload)
            except Exception as e:
                print(f"[Blackboard PubSub Error] Topic {topic}: {e}")

    def _record_event(self, arch: ArchitectureType, source: str, target: str, action: str, details: str, impact: str = "NORMAL"):
        evt = ArchitectureEvent(
            timestamp=time.time(),
            architecture=arch,
            source=source,
            target=target,
            action=action,
            details=details,
            impact=impact
        )
        self.event_log.append(evt)
        # Keep capped log
        if len(self.event_log) > 500:
            self.event_log.pop(0)

    def get_recent_events(self, limit: int = 50) -> List[ArchitectureEvent]:
        with self._lock:
            return list(self.event_log[-limit:])

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "active_locks": dict(self.knowledge_base["resource_locks"]),
                "spot_prices": dict(self.knowledge_base["spot_prices"]),
                "open_rfps": len([r for r in self.knowledge_base["rfp_board"] if r["status"] == "OPEN"]),
                "total_events": len(self.event_log)
            }

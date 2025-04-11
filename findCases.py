import numpy as np
from collections import defaultdict
import json
from datetime import datetime
from sentinels_web3 import upload_event_and_reward

class SpectrumAnalyzer:
    def __init__(self):
        self.history = defaultdict(list)
        self.abnormal_cases = []
        self.config = {
            'power_threshold': 3.0,  # dB above mean to consider as peak
            'high_power_threshold': -60.0,  # dB threshold for high power
            'unusual_frequency_threshold': 2.0,  # Standard deviations for unusual frequency
            'max_peaks_threshold': 15  # Maximum number of peaks to consider normal
        }

    def analyze_peaks(self, peak_freqs, peak_powers):
        """
        Analyze peaks for unusual patterns and store abnormal cases
        """
        if len(peak_freqs) == 0:
            return self._create_case("No peaks detected", "warning")

        # Calculate basic statistics
        mean_power = np.mean(peak_powers)
        std_power = np.std(peak_powers)
        mean_freq = np.mean(peak_freqs)
        std_freq = np.std(peak_freqs)

        # Check for unusual number of peaks
        if len(peak_freqs) > self.config['max_peaks_threshold']:
            return self._create_case(
                f"Too many peaks detected: {len(peak_freqs)}",
                "warning",
                {"num_peaks": len(peak_freqs)}
            )

        # Check for high power levels (less than -57 dB)
        high_powers = peak_powers[peak_powers > self.config['high_power_threshold']]
        if len(high_powers) > 0:
            return self._create_case(
                "High power levels detected",
                "alert",
                {
                    "threshold": self.config['high_power_threshold'],
                    "high_powers": high_powers.tolist(),
                    "frequencies": peak_freqs[peak_powers < self.config['high_power_threshold']].tolist()
                }
            )

        # Check for unusual frequency distribution
        unusual_freqs = peak_freqs[np.abs(peak_freqs - mean_freq) > self.config['unusual_frequency_threshold'] * std_freq]
        if len(unusual_freqs) > 0:
            return self._create_case(
                "Unusual frequency distribution detected",
                "alert",
                {
                    "mean_freq": mean_freq,
                    "std_freq": std_freq,
                    "unusual_freqs": unusual_freqs.tolist()
                }
            )

        return None

    def _create_case(self, description, severity, details=None):
        """Create a case record for an abnormal condition"""
        case = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "severity": severity,
            "details": details or {}
        }
        is_alert = severity != "warning"
        self.abnormal_cases.append(case)
        tx_hash = upload_event_and_reward(case, is_alert)
        return case

    def get_abnormal_cases(self, limit=10):
        """Get the most recent abnormal cases"""
        return self.abnormal_cases[-limit:]

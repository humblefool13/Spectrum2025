import os
import sys
import threading
import time
import json
os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, render_template, send_from_directory
from rtlsdr import RtlSdr
from scipy.signal import welch, find_peaks
import numpy as np
import matplotlib.pyplot as plt
import random
from findCases import SpectrumAnalyzer

app = Flask(__name__)

# Global variables to store the latest data
latest_peaks = []
last_update_time = 0
update_interval = 5  # seconds
spectrum_analyzer = SpectrumAnalyzer()
abnormal_cases = []

def process_sdr_data():
    global latest_peaks, last_update_time, abnormal_cases
    
    while True:
        try:
            # Run SDR scan
            sdr = RtlSdr()
            sdr.sample_rate = 2.4e6
            sdr.center_freq = 100e6
            sdr.gain = 'auto'
            samples = sdr.read_samples(256*1024)
            sdr.close()

            # Calculate PSD
            f, Pxx = welch(samples, fs=sdr.sample_rate, nperseg=1024)
            f_mhz = f / 1e6
            Pxx_db = 10 * np.log10(Pxx)

            # Peak detection
            mean_power = np.mean(Pxx_db)
            peaks, _ = find_peaks(Pxx_db, height=mean_power + 3.0, distance=10, prominence=0.5)
            peak_freqs = f_mhz[peaks]
            peak_powers = Pxx_db[peaks]

            # Update latest peaks
            latest_peaks = list(zip(peak_freqs, peak_powers))
            last_update_time = time.time()

            # Analyze for unusual cases
            case = spectrum_analyzer.analyze_peaks(peak_freqs, peak_powers)
            if case:
                abnormal_cases.append(case)
                # Save cases to file periodically
                if len(abnormal_cases) % 10 == 0:
                    spectrum_analyzer.save_cases()

            # Plot and save
            plt.figure(figsize=(10, 6))
            plt.plot(f_mhz, Pxx_db, label='PSD')
            plt.plot(peak_freqs, peak_powers, 'ro', label='Peaks')
            for i, pf in enumerate(peak_freqs):
                plt.annotate(f'{pf:.2f} GHz', xy=(pf, peak_powers[i]),
                             xytext=(10, 10), textcoords='offset points',
                             arrowprops=dict(arrowstyle='->'))
            plt.xlabel('Frequency (GHz)')
            plt.ylabel('Power (dB)')
            plt.title('RTL-SDR FFT (Live Scan)')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.savefig('static/spectrum.png')
            plt.close()

        except Exception as e:
            print(f"Error in SDR processing: {str(e)}")
        
        # Wait for the next update interval
        time.sleep(update_interval)

@app.route('/')
def index():
    return render_template(
        'index.html',
        peaks=latest_peaks,
        abnormal_cases=abnormal_cases[-5:],  # Show last 5 abnormal cases
        random=random.random
    )

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Start the SDR processing thread
    sdr_thread = threading.Thread(target=process_sdr_data, daemon=True)
    sdr_thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)))  # Make sure DLLs can be found

from rtlsdr import RtlSdr
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, welch

try:
    # Initialize SDR
    sdr = RtlSdr()
    print("RTL-SDR device initialized successfully")

    # SDR configuration
    sdr.sample_rate = 2.4e6       # Hz
    sdr.center_freq = 100e6       # Hz (FM band)
    sdr.gain = 'auto'

    print("Reading samples...")
    samples = sdr.read_samples(256*1024)
    print(f"Read {len(samples)} samples")

    sdr.close()
    print("SDR device closed")

    # Calculate Power Spectral Density (PSD)
    print("Calculating PSD using Welch method...")
    f, Pxx = welch(samples, fs=sdr.sample_rate, nperseg=1024)
    f_mhz = f / 1e6  # Convert to MHz
    Pxx_db = 10 * np.log10(Pxx)

    # Stats for thresholding
    mean_power = np.mean(Pxx_db)
    std_power = np.std(Pxx_db)
    max_power = np.max(Pxx_db)
    print(f"Mean power: {mean_power:.2f} dB")
    print(f"Std power: {std_power:.2f} dB")
    print(f"Max power: {max_power:.2f} dB")

    # Peak detection
    print("Finding peaks...")
    peaks, properties = find_peaks(
        Pxx_db,
        height=mean_power + 0.1,
        distance=5,
        prominence=0.05
    )

    print(f"Found {len(peaks)} peaks")
    if len(peaks) > 0:
        print("Peak frequencies (MHz):", f_mhz[peaks])
        print("Peak powers (dB):", Pxx_db[peaks])

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(f_mhz, Pxx_db, label='PSD')
    plt.plot(f_mhz[peaks], Pxx_db[peaks], 'ro', label='Peak Frequencies')

    for i, peak in enumerate(peaks):
        plt.annotate(f'{f_mhz[peak]:.2f} MHz',
                     xy=(f_mhz[peak], Pxx_db[peak]),
                     xytext=(10, 10), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->', lw=1))

    plt.title("RTL-SDR FFT (Peak Detection)")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Power Spectral Density (dB)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    print("Showing plot...")
    plt.show()

except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise

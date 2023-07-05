import customtkinter as ctk
import tkinter as tk
from tkinter import *
from tkinter import filedialog
import pydicom
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import os
import numpy as np
from skimage.filters import threshold_otsu
from skimage.segmentation import find_boundaries
import csv
from matplotlib.patches import Circle

class Application(ctk.CTk):
    def __init__(root):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        root.geometry("350x600")
        root.title("QC-MRI")
        root.iconbitmap('C:/Users/Sidik/OneDrive/Documents/Python/icon/QCMRI.ico')
        root.create_widgets()
        root.piu = None
        root.maxsignal = None 
        root.minsignal = None
        root.sg = None
        root.SNR = None
        root.aSNR = None
        
    #memilih file
    def select_dicom(root):
        filetypes = (("DICOM Files", "*.dcm"), ("All Files", "*.*"))
        root.dicom_path = filedialog.askopenfilename(filetypes=filetypes)

        if root.dicom_path:
            global dicom_data
            dicom_data = pydicom.dcmread(root.dicom_path)
            pixel_data = dicom_data.pixel_array
        elif root.dicom_path:
            dicom_data = None
            pixel_data =None
    
    #menampilkan citra       
    def tampilkandicom(root):
        dicom_data = pydicom.dcmread(root.dicom_path)
        pixel_data = dicom_data.pixel_array
        plt.imshow(pixel_data, cmap=plt.cm.gray)
        fig = plt.gcf()
        fig.canvas.manager.set_window_title('Citra MRI')
        plt.show()
            
    #Pengolahan PIU
    def PIU(root):
        global nilai_threshold
        dicom_data = pydicom.dcmread(root.dicom_path)
        pixel_data = dicom_data.pixel_array
        
        # Lakukan thresholding menggunakan metode Otsu
        threshold_value = threshold_otsu(pixel_data)
        binary_image = pixel_data > threshold_value + int(nilai_threshold)
        
        print("Nilai Threshold = ", threshold_value)
        # Dapatkan koordinat pinggiran ROI
        boundary_coords = find_boundaries(binary_image)

        # Dapatkan nilai sinyal hanya pada bagian objek
        signal_values = pixel_data[binary_image]

        max_signal = np.max(signal_values)
        min_signal = np.min(signal_values)
        print("Signal Max = ", max_signal)
        print("Signal Min = ", min_signal)

        roi_coords_max = np.where(pixel_data == max_signal)
        roi_coords_min = np.where(pixel_data == min_signal)

        # Menghitung PIU
        PIU = 100 * (1 - ((max_signal - min_signal) / (max_signal + min_signal)))
        root.piu = PIU
        root.maxsignal = max_signal
        root.minsignal = min_signal
        print("Nilai PIU =", PIU)
        
        # Lingkari ROI
        plt.imshow(pixel_data, cmap=plt.cm.gray)
    
        plt.contour(boundary_coords, colors='yellow', linewidths=1)
        
        circle_max = Circle((roi_coords_max[1][0], roi_coords_max[0][0]), radius=2, edgecolor='blue', facecolor='none', linewidth=2)
        circle_min = Circle((roi_coords_min[1][0], roi_coords_min[0][0]), radius=2, edgecolor='red', facecolor='none', linewidth=2)
        plt.gca().add_patch(circle_max)
        plt.gca().add_patch(circle_min)
        fig = plt.gcf()
        fig.canvas.manager.set_window_title('Pengujian PIU')
        plt.title('ROI 1 (Kuning) adalah wilayah Threshold \n ROI 2 (Biru) adalah letak signal maximum \n ROI 3 (Merah) adalah letak signal minimum')

        plt.show()
        root.TH = threshold_value

        
        
    #Pengolahan SG
    def SG(root):
        dicom_data = pydicom.dcmread(root.dicom_path)
        pixel_data = dicom_data.pixel_array
        pjk = 10
        l = 40
        yS = 140
        y_size = pixel_data.shape[0]
        x_size = pixel_data.shape[1]
        x = x_size/2
        y = y_size/2

        up = pixel_data[yS:yS+l, pjk:pjk+l]
        Sup = np.mean(up)
        #print ('S atas =', Sup)

        down = pixel_data[yS:yS+l, -pjk-l:-pjk]
        Sdown = np.mean(down)
        #print ('S bawah =', Sdown)

        left = pixel_data[pjk:pjk+l, yS:yS+l]
        Sleft = np.mean(left)
        #print ('S kanan =', Sleft)

        right = pixel_data[-pjk-l:-pjk, yS:yS+l]
        Sright = np.mean(right)
        #print ('S kiri =', Sright)

        middle = pixel_data[yS-l:yS+2*l, yS-l:yS+2*l]
        Smiddle = np.mean(middle)
        #print ('S tengah =', Smiddle)

        sg = abs (100*(((Sleft+Sright)-(Sup+Sdown))/(2*Smiddle)))

        print ("Nilai PSG (%) =", sg)
        root.sg = sg

        #Memunculkan gambar {SG}
        plt.imshow(pixel_data, cmap=plt.cm.gray)

        kotakatas = plt.Rectangle((yS, pjk), l, l, edgecolor='m', facecolor='none') 
        kotakbawah = plt.Rectangle((yS, y_size-pjk-l), l, l, edgecolor='m', facecolor='none')
        kotakkanan = plt.Rectangle((x_size-pjk-l,yS), l, l, edgecolor='m', facecolor='none')
        kotakkiri = plt.Rectangle((pjk,yS), l, l, edgecolor='m', facecolor='none')
        kotaktengah = plt.Rectangle((x-l, y-l), 2*l, 2*l, edgecolor='m', facecolor='none')

        fig = plt.gcf()
        plt.gca().add_patch(kotakatas)
        plt.gca().add_patch(kotakbawah)
        plt.gca().add_patch(kotakkanan)
        plt.gca().add_patch(kotakkiri)
        plt.gca().add_patch(kotaktengah)
        fig.canvas.manager.set_window_title('Pengujian Signal Ghosting')
        plt.title(f'SG = {sg}')
        plt.show()
        
    #Pengujian SNR otomatis
    def asnr(root):
        dicom_data = pydicom.dcmread(root.dicom_path)
        pixel_data = dicom_data.pixel_array
        y_size = pixel_data.shape[0]
        x_size = pixel_data.shape[1]
        # Menampilkan citra DICOM
        plt.imshow(pixel_data, cmap=plt.cm.gray)
        
        x = x_size/2
        y = y_size/2
        pjk = 10
        r = 40
        roi = Circle((x, y), r, fill=False, edgecolor='r')

        # Membuat mask lingkaran {SNR}
        Y,X = np.ogrid[:x_size, :y_size]
        mask = ((X - x)**2 + (Y - y)**2 <= r**2)

        # Ambil pixel data berbentuk bulat dari matriks {SNR}
        bulat = pixel_data[mask]
        mean_signal = np.mean(bulat)
        print('Signal (ROI 1)=', mean_signal)

        # Menentukan ROI background {SNR}
        pjk = 40
        width = 40
        height = 40
        bkg = pixel_data[pjk:r+pjk, pjk:r+pjk]
        kotak = plt.Rectangle((pjk, pjk), width, height, edgecolor='b', facecolor='none')
        std_noise = np.std(bkg)
        print('STD (ROI 2)=', std_noise)

        # Menentukan nilai {SNR}
        N = 0.655*mean_signal
        aSNR = N/std_noise
        print("Nilai SNR (Otomatis) =",aSNR)
        root.aSNR = aSNR

        # Menampilkan plot dengan ROI {SNR}
        fig = plt.gcf()
        plt.gca().add_patch(roi)
        plt.gca().add_patch(kotak)
        fig.canvas.manager.set_window_title('Pengujian SNR Otomatis')
        plt.title(f'SNR = {aSNR}')
        plt.show()
        
    #Perhitungan SNR manual
    def ujisnr(root):
        global snr
        dicom_data = pydicom.dcmread(root.dicom_path)
        pixel_data = dicom_data.pixel_array
        nilai_Roix = int(valuex)
        nilai_Roiy = int(valuey)
        
        if pixel_data is not None:
            # Menampilkan gambar DICOM
            fig, ax = plt.subplots()
            image = ax.imshow(pixel_data, cmap=plt.cm.gray)

            def calculate_mean_signal(roi):
                mean_signal = np.mean(roi)
                return mean_signal

            def calculate_std_signal(roi):
                std_signal = np.std(roi)
                return std_signal

            def calculate_snr(mean_signal, std_signal):
                snr = (mean_signal*0.655) / std_signal
                return snr

            def update_roi1(x, y):
                global roi1
                roi1 = None
                
                # Hapus ROI 1 sebelumnya (jika ada)
                if roi1 is not None:
                    roi1.remove()

                # Hitung ROI 1
                roi1 = plt.Rectangle((x, y), nilai_Roix, nilai_Roiy, linewidth=1, edgecolor='r', facecolor='none')

                # Tambahkan ROI 1 ke plot
                ax.add_patch(roi1)
                plt.draw()

                # Hitung dan cetak mean signal pada ROI 1
                mean_signal = calculate_mean_signal(pixel_data[y:y+nilai_Roiy, x:x+nilai_Roix])
                print("Mean Signal (ROI 1) =", mean_signal)

            def update_roi2(x, y):
                global roi2
                roi2 = None
                
                # Hapus ROI 2 sebelumnya (jika ada)
                if roi2 is not None:
                    roi2.remove()

                # Hitung ROI 2
                roi2 = plt.Rectangle((x, y), nilai_Roix, nilai_Roiy, linewidth=1, edgecolor='b', facecolor='none')

                # Tambahkan ROI 2 ke plot
                ax.add_patch(roi2)
                plt.draw()

                # Hitung dan cetak std signal pada ROI 2
                std_signal = calculate_std_signal(pixel_data[y:y+nilai_Roiy, x:x+nilai_Roix])
                print("Std Signal (ROI 2) =", std_signal)

            def on_click(event):
                global roi2_std_signal, roi1_mean_signal, snr
                x = int(event.xdata)
                y = int(event.ydata)

                if event.button == 1:  # Klik kiri untuk mengupdate ROI 1
                    update_roi1(x, y)
                    roi1_mean_signal = calculate_mean_signal(pixel_data[int(event.ydata):int(event.ydata)+nilai_Roiy, int(event.xdata):int(event.xdata)+nilai_Roix])
                
                elif event.button == 3:  # Klik kanan untuk mengupdate ROI 2
                    update_roi2(x, y)

                    # Hitung SNR dari mean signal ROI 1 dan std signal ROI 2
                    roi2_std_signal = calculate_std_signal(pixel_data[int(event.ydata):int(event.ydata)+nilai_Roiy, int(event.xdata):int(event.xdata)+nilai_Roix])
                    
                    if roi1_mean_signal is not None:
                        print('SNR (Manual) =', calculate_snr(roi1_mean_signal,roi2_std_signal))
                        snr = calculate_snr(roi1_mean_signal,roi2_std_signal)

            # Mendaftarkan fungsi on_click sebagai event handler
            cid = fig.canvas.mpl_connect('button_press_event', on_click)

            # Menampilkan gambar
            fig = plt.gcf()
            fig.canvas.manager.set_window_title('Pengujian SNR Manual')
            plt.title('Klik kiri untuk mengupdate ROI 1 (Merah) & \n Klik kanan untuk mengupdate ROI 2 (Biru)')
            plt.show()
        root.SNR = snr 
    
    #menyimpan data
    def save_to_csv(root):
        filetypes = [("CSV Files", "*.csv"), ("All Files", "*.*")]
        file_path = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=".csv")

        if file_path:
            with open(file_path, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file)

                # Menulis data ke file CSV
                writer.writerow(["PIU (%)", "Nilai Threshold","Signal Max","Signal Min", "PSG (%)", "SNR Manual", "SNR Otomatis"])  # Menulis header
                writer.writerow([root.piu, root.TH, root.maxsignal, root.minsignal, root.sg, root.SNR, root.aSNR])  # Menulis data dari perhitungan
    def reset(root):
        dicom_data.clear()
            
    def create_widgets(root):
        #Membuat tombol pilih file
        root.btn_file_dcm = ctk.CTkButton(root, text="Pilih File DICOM", font=("Roboto", 15), command=root.select_dicom)
        root.btn_file_dcm.pack(pady=10, padx=1)   
        
        #Tombol gambar
        root.btn_image = ctk.CTkButton(root, text="Tampilkan Citra", font=("Roboto", 15), command=root.tampilkandicom)
        root.btn_image.pack(pady=10, padx=1) 
        
        #Slicer Roi
        labelx = ctk.CTkLabel(root, text="Lebar Roi: ")
        labelx.pack(pady=10)
        
        def update_valuex(root):
            global valuex, nilai_Roix
            valuex = scalex.get()  # Mendapatkan nilai geser dari skala
            labelx.configure(text="Lebar ROI: " + str(valuex))  # Menampilkan nilai pada label
            nilai_Roix = valuex
            
        scalex = ctk.CTkSlider(root, from_=0, to=100, number_of_steps=40, command=update_valuex)
        scalex.pack()
        
        labely = ctk.CTkLabel(root, text="Tinggi Roi: ")
        labely.pack(pady=10)
        
        def update_valuex(root):
            global valuey, nilai_Roiy
            valuey = scaley.get()  # Mendapatkan nilai geser dari skala
            labely.configure(text="Tinggi Roi: " + str(valuey))  # Menampilkan nilai pada label
            nilai_Roiy = valuey
        
        scaley = ctk.CTkSlider(root, from_=0, to=100, number_of_steps=40, command=update_valuex)
        scaley.pack()
        
        #Tombol SNR
        root.btn_SNR = ctk.CTkButton(root, text="SNR Manual", font=("Roboto", 15), command=root.ujisnr)
        root.btn_SNR.pack(pady=10, padx=1)
        
        root.btn_asnr = ctk.CTkButton(root, text="SNR otomatis", font=("Roboto", 15), command=root.asnr)
        root.btn_asnr.pack(pady=10, padx=1)
        
        #Tombol SG
        root.btn_SG = ctk.CTkButton(root, text="Signal Ghosting", font=("Roboto", 15), command=root.SG)
        root.btn_SG.pack(pady=10, padx=1) 
        
        #Slider Threshold PIU
        label_PIU = ctk.CTkLabel(root, text="Threshold PIU: ")
        label_PIU.pack(pady=10)
        
        def update_valuePIU(root):
            global value_threshold, nilai_threshold
            value_threshold = scale_PIU.get()  # Mendapatkan nilai geser dari skala
            nilai_threshold = value_threshold
            label_PIU.configure(text="Threshold PIU: " + str(value_threshold))  # Menampilkan nilai pada label
 
        
        scale_PIU = ctk.CTkSlider(root, from_=0, to=1000, number_of_steps=40, command=update_valuePIU)
        scale_PIU.pack()
        
        #Tombol PIU
        root.btn_PIU = ctk.CTkButton(root, text="PIU", font=("Roboto", 15), command=root.PIU)
        root.btn_PIU.pack(pady=10, padx=1)

        #Tombol Save Data
        root.btn_Save = ctk.CTkButton(root, text="Save", font=("Roboto", 15), command=root.save_to_csv)
        root.btn_Save.pack(pady=10, padx=1)
        
        #Tombol Reset
        root.btn_reset = ctk.CTkButton(root, text="Reset", font=("Roboto", 15), command=root.reset)
        root.btn_reset.pack(pady=10, padx=1)
        
        
        
 
Application().mainloop()

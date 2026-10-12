"""Draw the learning pipeline; this picture explains the implemented experiment."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

root=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(figsize=(13,15),dpi=140)
fig.patch.set_facecolor('#f5f7fb'); ax.set_facecolor('#f5f7fb')
ax.set_xlim(0,13);ax.set_ylim(0,15);ax.axis('off')
ax.text(6.5,14.55,'DARI DATA KE KEPUTUSAN ALOKASI',ha='center',weight='bold',fontsize=20,color='#14233f')
ax.text(6.5,14.15,'Kasus: bagaimana membagi dana ke beberapa aset?',ha='center',fontsize=14,color='#45556e')

def box(x,y,w,h,title,body,color='#fff',border='#bdc9da',title_size=14,body_size=12):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.10,rounding_size=0.12',
                          linewidth=1.4,edgecolor=border,facecolor=color))
 ax.text(x+w/2,y+h-.24,title,ha='center',va='top',weight='bold',fontsize=title_size,color='#14233f')
 ax.text(x+w/2,y+h-.62,body,ha='center',va='top',fontsize=body_size,color='#334764',linespacing=1.45)

def arrow(x1,y1,x2,y2):
 ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops={'arrowstyle':'-|>','color':'#687c99','lw':1.7})

box(2.1,12.45,8.8,1.2,'1. DATA MASUK','Harga historis / return harian / demo sintetis\nBaris = tanggal; kolom = aset')
arrow(6.5,12.33,6.5,11.98)
box(2.1,10.70,8.8,1.18,'2. VALIDASI DAN PEMISAHAN WAKTU','Tanggal unik, satuan desimal, tidak ada data kosong\nTrain 60% → validation 20% → test 20%',color='#eaf2ff')
arrow(6.5,10.58,6.5,10.23)
box(2.1,8.93,8.8,1.2,'3. REPRESENTASI NUMERIK MASALAH','Dari data sebelum test: return tahunan dan kovarians\nAturan: target return, batas bobot, total dana = 100%')
arrow(6.5,8.81,6.5,8.45)
# At this branch, all optimizers receive the same pre-test problem.
for x,center in [(.3,2.3),(4.5,6.5),(8.7,10.7)]:
 arrow(6.5,8.45,center,7.91)
box(.3,6.14,4,1.62,'4A. KLASIK','Heuristik: tambah dana sedikit demi sedikit\nSolver, random, SA, steepest, tabu',body_size=10.5,color='#e8f6ef',title_size=12)
box(4.5,6.14,4,1.62,'4B. AI','Belajar statistik → bobot dari solver\nTrain: belajar; validation: pilih model\nPelengkap: AI sebagai awal solver',body_size=10.5,color='#fff3df',title_size=12)
box(8.7,6.14,4,1.62,'4C. QAOA SIMULATOR','Masalah diubah menjadi biaya QUBO\nSimulasi mencari kandidat bobot\nBerjalan pada komputer klasik',body_size=10.5,color='#f1eaff',title_size=12)
for x in [2.3,6.5,10.7]:arrow(x,6.02,6.5,5.59)
box(2.1,4.25,8.8,1.22,'5. PERIKSA KELAYAKAN HASIL','Bobot ≥ 0; total = 100%; bobot ≤ batas; return ≥ target\nHasil gagal tetap dilaporkan, tidak dipakai untuk evaluasi test',color='#fff0ef')
arrow(6.5,4.13,6.5,3.78)
box(2.1,2.47,8.8,1.2,'6. BANDINGKAN DAN EVALUASI','Pada history: varians, kelayakan, waktu dan biaya training\nPada test: return aktual, fluktuasi dan penurunan maksimum')
arrow(6.5,2.35,6.5,2.00)
box(2.1,.70,8.8,1.18,'7. OUTPUT YANG DIBACA PENGGUNA','Tabel bobot dana + tabel perbandingan + alasan gagal\nNotebook / FastAPI → PostgreSQL → dashboard',color='#eaf2ff')
ax.text(6.5,.23,'AI memakai label solver dari train/validation; data test tidak dipakai untuk belajar atau membuat alokasi.',
        ha='center',fontsize=10,color='#45556e')
fig.savefig(root/'docs/images/learning_pipeline.png',bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close(fig)
print('Learning pipeline image created')

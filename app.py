"""
Pemesanan Tiket Event - desktop app
Default: SQLite (langsung bisa dicoba). MySQL/XAMPP: set USE_MYSQL=1 dan isi DB_* di .env.
"""
import os, sqlite3, secrets, string, hashlib, hmac, csv, shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "event_ticket.db")
BG = "#0b1220"; PANEL = "#121e32"; PANEL2 = "#192943"
ACCENT = "#22d3ee"; BLUE = "#3b82f6"; TEXT = "#edf5ff"; MUTED = "#9fb2cc"
GREEN = "#34d399"; RED = "#fb7185"

def password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class Database:
    def __init__(self):
        self.mysql = os.getenv("USE_MYSQL", "0") == "1"
        if self.mysql:
            try:
                import mysql.connector
                self.cnx = mysql.connector.connect(
                    host=os.getenv("DB_HOST","127.0.0.1"),
                    port=int(os.getenv("DB_PORT","3306")),
                    user=os.getenv("DB_USER","root"),
                    password=os.getenv("DB_PASSWORD",""),
                    database=os.getenv("DB_NAME","db_tiket_event")
                )
                self.cur = self.cnx.cursor(dictionary=True)
                self.init_mysql()
            except Exception as e:
                raise RuntimeError("Koneksi MySQL gagal. Pastikan MySQL XAMPP aktif, database dibuat, dan .env benar.\\n\\n"+str(e))
        else:
            self.cnx = sqlite3.connect(DB_FILE)
            self.cnx.row_factory = sqlite3.Row
            self.cur = self.cnx.cursor()
            self.init_sqlite()

    def init_sqlite(self):
        self.cur.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'Admin');
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, venue TEXT, event_date TEXT, description TEXT);
        CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER, name TEXT, price REAL, quota INTEGER);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, customer TEXT, phone TEXT, event_id INTEGER, category_id INTEGER, qty INTEGER, total REAL, order_date TEXT);
        CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, method TEXT, status TEXT, paid_at TEXT);
        """)
        self.cnx.commit()
        self.cur.execute("SELECT COUNT(*) n FROM users")
        if self.cur.fetchone()["n"] == 0:
            self.cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",("admin",password_hash("admin123"),"Admin"))
            self.cnx.commit()
        self.cur.execute("SELECT COUNT(*) n FROM events")
        if self.cur.fetchone()["n"] == 0:
            self.cur.execute("INSERT INTO events(name,venue,event_date,description) VALUES(?,?,?,?)",
                ("Festival Kreatif 2026","Aula Serbaguna","2026-12-20","Contoh data event"))
            eid=self.cur.lastrowid
            self.cur.executemany("INSERT INTO categories(event_id,name,price,quota) VALUES(?,?,?,?)",
                [(eid,"Regular",50000,300),(eid,"VIP",100000,100),(eid,"VVIP",175000,40)])
            self.cnx.commit()

    def init_mysql(self):
        # Tabel dibuat dari schema_mysql.sql. Buat akun admin pertama melalui aplikasi jika tabel users kosong.
        self.cur.execute("SELECT COUNT(*) AS n FROM users")
        if self.cur.fetchone()["n"] == 0:
            self.execute("INSERT INTO users(username,password,role) VALUES(%s,%s,%s)",("admin",password_hash("admin123"),"Admin"))
            self.cnx.commit()

    def execute(self, sql, params=()):
        if not self.mysql:
            sql=sql.replace("%s","?")
        self.cur.execute(sql, params)
        return self.cur

    def all(self, sql, params=()):
        return self.execute(sql,params).fetchall()

    def one(self, sql, params=()):
        return self.execute(sql,params).fetchone()

    def commit(self): self.cnx.commit()
    def close(self): self.cnx.close()

class TicketApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EVENTLY | Sistem Pemesanan Tiket")
        self.geometry("1240x780"); self.minsize(1050,680); self.configure(bg=BG)
        try: self.db=Database()
        except Exception as e:
            messagebox.showerror("Database",str(e)); self.destroy(); return
        self.style=ttk.Style(self); self.style.theme_use("clam")
        self.style.configure("Treeview",background=PANEL,foreground=TEXT,fieldbackground=PANEL,rowheight=31,borderwidth=0)
        self.style.configure("Treeview.Heading",background=PANEL2,foreground=ACCENT,font=("Segoe UI",10,"bold"),relief="flat")
        self.style.map("Treeview",background=[("selected","#1d4ed8")])
        self.login_screen()

    def clear(self):
        for w in self.winfo_children(): w.destroy()

    def label(self,parent,text,size=10,color=TEXT,bold=False):
        return tk.Label(parent,text=text,bg=parent.cget("bg"),fg=color,font=("Segoe UI",size,"bold" if bold else "normal"))

    def button(self,parent,text,command,primary=False):
        return tk.Button(parent,text=text,command=command,bg=ACCENT if primary else PANEL2,
            fg="#071522" if primary else TEXT,activebackground=BLUE,activeforeground="white",
            relief="flat",bd=0,padx=15,pady=9,cursor="hand2",font=("Segoe UI",10,"bold"))

    def entry(self,parent,width=28):
        e=tk.Entry(parent,width=width,bg="#0d192b",fg=TEXT,insertbackground=TEXT,relief="flat",
                   highlightthickness=1,highlightbackground="#2b405e",highlightcolor=ACCENT,font=("Segoe UI",10))
        e.pack(ipady=9,padx=2,pady=5); return e

    def login_screen(self):
        self.clear()
        wrap=tk.Frame(self,bg=BG); wrap.pack(fill="both",expand=True)
        left=tk.Frame(wrap,bg="#101f36",width=590); left.pack(side="left",fill="both"); left.pack_propagate(False)
        tk.Label(left,text="EVENTLY",bg="#101f36",fg=ACCENT,font=("Segoe UI",18,"bold")).place(x=55,y=55)
        tk.Label(left,text="Atur event.\nJual tiket.\nKelola semuanya.",bg="#101f36",fg=TEXT,
                 font=("Segoe UI",32,"bold"),justify="left").place(x=55,y=160)
        tk.Label(left,text="Sistem manajemen pemesanan tiket event",bg="#101f36",fg=MUTED,
                 font=("Segoe UI",12)).place(x=58,y=335)
        tk.Label(left,text="●  Data event   ●  Pemesanan   ●  Laporan",bg="#101f36",fg=ACCENT,
                 font=("Segoe UI",10)).place(x=58,y=390)
        right=tk.Frame(wrap,bg=BG); right.pack(side="right",fill="both",expand=True)
        box=tk.Frame(right,bg=PANEL,padx=42,pady=38); box.place(relx=.5,rely=.5,anchor="center")
        tk.Label(box,text="Selamat datang",bg=PANEL,fg=TEXT,font=("Segoe UI",23,"bold")).pack(anchor="w")
        tk.Label(box,text="Masuk untuk melanjutkan ke dashboard",bg=PANEL,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w",pady=(5,25))
        tk.Label(box,text="USERNAME",bg=PANEL,fg=ACCENT,font=("Segoe UI",9,"bold")).pack(anchor="w")
        self.user=self.entry(box,32)
        tk.Label(box,text="PASSWORD",bg=PANEL,fg=ACCENT,font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(12,0))
        self.pwd=self.entry(box,32); self.pwd.config(show="•")
        self.button(box,"MASUK  →",self.login,True).pack(fill="x",pady=(22,10))
        tk.Label(box,text="Demo login: admin  /  admin123",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w")
        self.user.focus_set(); self.bind("<Return>",lambda e:self.login())

    def login(self):
        u=self.user.get().strip(); p=password_hash(self.pwd.get())
        row=self.db.one("SELECT * FROM users WHERE username=%s AND password=%s",(u,p))
        if row: self.dashboard(row)
        else: messagebox.showerror("Login gagal","Username atau password tidak sesuai.")

    def dashboard(self,user):
        self.unbind("<Return>"); self.clear()
        shell=tk.Frame(self,bg=BG); shell.pack(fill="both",expand=True)
        side=tk.Frame(shell,bg="#0e1a2d",width=225); side.pack(side="left",fill="y"); side.pack_propagate(False)
        tk.Label(side,text="EVENTLY",bg="#0e1a2d",fg=ACCENT,font=("Segoe UI",20,"bold")).pack(anchor="w",padx=24,pady=(28,2))
        tk.Label(side,text="EVENT MANAGEMENT",bg="#0e1a2d",fg=MUTED,font=("Segoe UI",8,"bold")).pack(anchor="w",padx=26,pady=(0,30))
        self.content=tk.Frame(shell,bg=BG); self.content.pack(side="right",fill="both",expand=True)
        for name,fn in [("▦  Dashboard",self.home),("▣  Data Event",self.events),("◈  Kategori Tiket",self.categories),("＋  Pemesanan",self.orders),("▤  Laporan Penjualan",self.reports),("⇧  Ekspor Excel / PDF",self.export_page)]:
            self.button(side,name,fn).pack(fill="x",padx=13,pady=5)
        tk.Frame(side,bg="#263953",height=1).pack(fill="x",padx=18,pady=22)
        tk.Label(side,text=f"Login: {user['username']}",bg="#0e1a2d",fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=24)
        self.button(side,"Keluar akun",self.login_screen).pack(fill="x",padx=13,pady=12)
        self.home()

    def heading(self,title,sub):
        for w in self.content.winfo_children(): w.destroy()
        top=tk.Frame(self.content,bg=BG); top.pack(fill="x",padx=30,pady=(27,20))
        tk.Label(top,text=title,bg=BG,fg=TEXT,font=("Segoe UI",23,"bold")).pack(anchor="w")
        tk.Label(top,text=sub,bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w",pady=4)
        return top

    def card(self,parent,title,value,accent=ACCENT):
        f=tk.Frame(parent,bg=PANEL,padx=20,pady=17,highlightthickness=1,highlightbackground="#203550")
        tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w")
        tk.Label(f,text=value,bg=PANEL,fg=accent,font=("Segoe UI",22,"bold")).pack(anchor="w",pady=(8,0))
        return f

    def home(self):
        self.heading("Dashboard","Ringkasan aktivitas penjualan tiket event.")
        row=tk.Frame(self.content,bg=BG); row.pack(fill="x",padx=30)
        n_event=self.db.one("SELECT COUNT(*) n FROM events")["n"]
        n_order=self.db.one("SELECT COUNT(*) n FROM orders")["n"]
        qty=self.db.one("SELECT COALESCE(SUM(qty),0) n FROM orders")["n"]
        revenue=self.db.one("SELECT COALESCE(SUM(total),0) n FROM orders")["n"]
        for t,v,c in [("Total Event",n_event,ACCENT),("Transaksi",n_order,BLUE),("Tiket Terjual",qty,GREEN),("Pendapatan",f"Rp {revenue:,.0f}", "#fbbf24")]:
            self.card(row,t,v,c).pack(side="left",fill="x",expand=True,padx=(0,12))
        panel=tk.Frame(self.content,bg=PANEL,padx=22,pady=20); panel.pack(fill="both",expand=True,padx=30,pady=24)
        tk.Label(panel,text="Transaksi terbaru",bg=PANEL,fg=TEXT,font=("Segoe UI",14,"bold")).pack(anchor="w",pady=(0,12))
        self.table(panel,("Kode Tiket","Pelanggan","Event","Jumlah","Total","Tanggal"),
            self.db.all("SELECT o.code,o.customer,e.name event,o.qty,o.total,o.order_date FROM orders o LEFT JOIN events e ON e.id=o.event_id ORDER BY o.id DESC LIMIT 8"),
            (("code","Kode Tiket"),("customer","Pelanggan"),("event","Event"),("qty","Jumlah"),("total","Total"),("order_date","Tanggal")))

    def table(self,parent,cols,rows,mapping=None):
        frame=tk.Frame(parent,bg=PANEL); frame.pack(fill="both",expand=True)
        tree=ttk.Treeview(frame,columns=cols,show="headings",height=12)
        for c in cols: tree.heading(c,text=c); tree.column(c,width=max(100,int(760/len(cols))),anchor="w")
        tree.pack(fill="both",expand=True)
        for r in rows:
            if mapping:
                vals=[]
                for key,label in mapping:
                    val=r[key]
                    if key in ("total","price"): val=f"Rp {float(val):,.0f}"
                    vals.append(val)
            else:
                # Tanpa mapping, tampilkan semua kolom sesuai urutan SELECT.
                vals=list(r)
            tree.insert("","end",values=vals)
        return tree

    def events(self):
        self.heading("Data Event","Kelola informasi acara yang akan dijual tiketnya.")
        form=tk.Frame(self.content,bg=PANEL,padx=18,pady=14); form.pack(fill="x",padx=30)
        fields=[]
        for label in ["Nama event","Lokasi","Tanggal (YYYY-MM-DD)","Deskripsi"]:
            tk.Label(form,text=label,bg=PANEL,fg=MUTED).pack(side="left",padx=(0,5))
            e=tk.Entry(form,width=17,bg="#0d192b",fg=TEXT,insertbackground=TEXT,relief="flat"); e.pack(side="left",ipady=7,padx=(0,12)); fields.append(e)
        def save():
            vals=[e.get().strip() for e in fields]
            if not vals[0] or not vals[1] or not vals[2]: return messagebox.showwarning("Validasi","Nama, lokasi, dan tanggal wajib diisi.")
            try: datetime.strptime(vals[2],"%Y-%m-%d")
            except: return messagebox.showwarning("Tanggal","Gunakan format YYYY-MM-DD.")
            self.db.execute("INSERT INTO events(name,venue,event_date,description) VALUES(%s,%s,%s,%s)",vals); self.db.commit(); self.events()
        self.button(form,"＋ Tambah",save,True).pack(side="left")
        rows=self.db.all("SELECT * FROM events ORDER BY id DESC")
        panel=tk.Frame(self.content,bg=PANEL,padx=18,pady=16); panel.pack(fill="both",expand=True,padx=30,pady=18)
        tree=self.table(panel,("ID","Nama Event","Lokasi","Tanggal","Deskripsi"),rows)
        def delete():
            sel=tree.selection()
            if not sel:return
            ident=tree.item(sel[0])["values"][0]
            if messagebox.askyesno("Hapus","Hapus event terpilih?"):
                self.db.execute("DELETE FROM events WHERE id=%s",(ident,)); self.db.commit(); self.events()
        self.button(panel,"Hapus event terpilih",delete).pack(anchor="e",pady=8)

    def categories(self):
        self.heading("Kategori Tiket","Atur jenis tiket, harga, dan kuota untuk setiap event.")
        form=tk.Frame(self.content,bg=PANEL,padx=18,pady=15); form.pack(fill="x",padx=30)
        evs=self.db.all("SELECT * FROM events")
        if not evs: tk.Label(form,text="Tambahkan event terlebih dahulu.",bg=PANEL,fg=TEXT).pack(); return
        tk.Label(form,text="Event",bg=PANEL,fg=MUTED).pack(side="left")
        ev=tk.StringVar(value=str(evs[0]["id"])); ttk.Combobox(form,textvariable=ev,values=[f'{x["id"]} - {x["name"]}' for x in evs],width=22).pack(side="left",padx=8)
        name=tk.Entry(form,width=16); price=tk.Entry(form,width=12); quota=tk.Entry(form,width=10)
        for lab,w in [("Kategori",name),("Harga",price),("Kuota",quota)]:
            tk.Label(form,text=lab,bg=PANEL,fg=MUTED).pack(side="left",padx=(10,3)); w.pack(side="left",ipady=7,padx=3)
        def save():
            try:
                eid=int(ev.get().split(" - ")[0]); pr=float(price.get()); q=int(quota.get())
                if not name.get().strip() or pr<0 or q<0: raise ValueError()
                self.db.execute("INSERT INTO categories(event_id,name,price,quota) VALUES(%s,%s,%s,%s)",(eid,name.get().strip(),pr,q)); self.db.commit(); self.categories()
            except: messagebox.showwarning("Validasi","Isi kategori, harga angka, dan kuota angka dengan benar.")
        self.button(form,"Tambah kategori",save,True).pack(side="left",padx=8)
        rows=self.db.all("SELECT c.id,e.name event,c.name kategori,c.price,c.quota FROM categories c LEFT JOIN events e ON e.id=c.event_id")
        panel=tk.Frame(self.content,bg=PANEL,padx=18,pady=16); panel.pack(fill="both",expand=True,padx=30,pady=18)
        self.table(panel,("ID","Event","Kategori","Harga","Kuota"),rows,(("id","ID"),("event","Event"),("kategori","Kategori"),("price","Harga"),("quota","Kuota")))

    def orders(self):
        self.heading("Pemesanan Tiket","Buat transaksi baru dan hasilkan kode tiket otomatis.")
        evs=self.db.all("SELECT * FROM events")
        if not evs: tk.Label(self.content,text="Tambahkan event dahulu.",bg=BG,fg=TEXT).pack(); return
        box=tk.Frame(self.content,bg=PANEL,padx=24,pady=22); box.pack(fill="x",padx=30)
        def field(label):
            tk.Label(box,text=label,bg=PANEL,fg=MUTED).pack(anchor="w",pady=(7,0))
            e=tk.Entry(box,bg="#0d192b",fg=TEXT,insertbackground=TEXT,relief="flat"); e.pack(fill="x",ipady=8); return e
        customer=field("Nama pelanggan"); phone=field("Nomor telepon")
        tk.Label(box,text="Pilih event",bg=PANEL,fg=MUTED).pack(anchor="w",pady=(8,0))
        evvar=tk.StringVar(value=f'{evs[0]["id"]} - {evs[0]["name"]}')
        ttk.Combobox(box,textvariable=evvar,state="readonly",values=[f'{x["id"]} - {x["name"]}' for x in evs]).pack(fill="x",ipady=5)
        tk.Label(box,text="Kategori tiket",bg=PANEL,fg=MUTED).pack(anchor="w",pady=(8,0))
        cats=self.db.all("SELECT * FROM categories WHERE event_id=%s",(evs[0]["id"],))
        catvar=tk.StringVar(value="")
        catbox=ttk.Combobox(box,textvariable=catvar,state="readonly",values=[f'{c["id"]} - {c["name"]} | Rp {c["price"]:,.0f} | sisa {c["quota"]}' for c in cats]); catbox.pack(fill="x",ipady=5)
        def loadcats(*_):
            eid=int(evvar.get().split(" - ")[0]); cc=self.db.all("SELECT * FROM categories WHERE event_id=%s",(eid,))
            catbox["values"]=[f'{c["id"]} - {c["name"]} | Rp {c["price"]:,.0f} | sisa {c["quota"]}' for c in cc]
            catvar.set(catbox["values"][0] if cc else "")
        evvar.trace_add("write",loadcats)
        qty=field("Jumlah tiket")
        def save():
            try:
                eid=int(evvar.get().split(" - ")[0]); cid=int(catvar.get().split(" - ")[0]); q=int(qty.get())
                cat=self.db.one("SELECT * FROM categories WHERE id=%s",(cid,))
                if not customer.get().strip() or q<1 or not cat or q>cat["quota"]: raise ValueError()
                code="EVT-"+datetime.now().strftime("%y%m%d")+"-"+''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(5))
                total=float(cat["price"])*q
                self.db.execute("INSERT INTO orders(code,customer,phone,event_id,category_id,qty,total,order_date) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (code,customer.get().strip(),phone.get().strip(),eid,cid,q,total,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                oid=self.db.cur.lastrowid
                self.db.execute("UPDATE categories SET quota=quota-%s WHERE id=%s",(q,cid))
                self.db.execute("INSERT INTO payments(order_id,method,status,paid_at) VALUES(%s,%s,%s,%s)",(oid,"Tunai","Lunas",datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                self.db.commit()
                messagebox.showinfo("Pemesanan berhasil",f"Kode tiket: {code}\\nTotal: Rp {total:,.0f}")
                self.orders()
            except Exception as e: messagebox.showwarning("Pemesanan gagal","Periksa nama, kategori, jumlah, dan kuota tiket.\\n"+str(e))
        self.button(box,"PROSES PEMESANAN",save,True).pack(anchor="e",pady=18)

    def reports(self):
        self.heading("Laporan Penjualan","Pantau transaksi, jumlah tiket, dan total pendapatan.")
        rows=self.db.all("SELECT o.code,o.customer,e.name event,c.name kategori,o.qty,o.total,o.order_date FROM orders o LEFT JOIN events e ON e.id=o.event_id LEFT JOIN categories c ON c.id=o.category_id ORDER BY o.id DESC")
        total=self.db.one("SELECT COALESCE(SUM(total),0) n FROM orders")["n"]
        tk.Label(self.content,text=f"TOTAL PENDAPATAN     Rp {total:,.0f}",bg=PANEL,fg=GREEN,font=("Segoe UI",17,"bold"),padx=20,pady=17).pack(fill="x",padx=30)
        panel=tk.Frame(self.content,bg=PANEL,padx=18,pady=16); panel.pack(fill="both",expand=True,padx=30,pady=18)
        self.table(panel,("Kode","Pelanggan","Event","Kategori","Qty","Total","Tanggal"),rows)

    def export_page(self):
        self.heading("Ekspor & Backup","Unduh laporan ke Excel (.xlsx) atau PDF, dan backup database.")
        box=tk.Frame(self.content,bg=PANEL,padx=28,pady=28); box.pack(fill="x",padx=30)
        tk.Label(box,text="Ekspor laporan penjualan",bg=PANEL,fg=TEXT,font=("Segoe UI",15,"bold")).pack(anchor="w",pady=(0,12))
        self.button(box,"⇩  Export Excel (.xlsx)",self.export_excel,True).pack(anchor="w",pady=6)
        self.button(box,"⇩  Export PDF",self.export_pdf).pack(anchor="w",pady=6)
        self.button(box,"▣  Backup database",self.backup).pack(anchor="w",pady=6)
        tk.Label(box,text="File ekspor berisi kode tiket, pelanggan, event, kategori, jumlah, total, dan tanggal transaksi.",bg=PANEL,fg=MUTED).pack(anchor="w",pady=(14,0))

    def report_data(self):
        return self.db.all("SELECT o.code,o.customer,o.phone,e.name event,c.name kategori,o.qty,o.total,o.order_date FROM orders o LEFT JOIN events e ON e.id=o.event_id LEFT JOIN categories c ON c.id=o.category_id ORDER BY o.id")

    def export_excel(self):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            path=filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel Workbook","*.xlsx")],initialfile="laporan_penjualan.xlsx")
            if not path:return
            wb=Workbook(); ws=wb.active; ws.title="Penjualan"
            headers=["Kode Tiket","Pelanggan","Telepon","Event","Kategori","Jumlah","Total","Tanggal"]
            ws.append(headers)
            for c in ws[1]:
                c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill("solid",fgColor="17365D")
            for r in self.report_data(): ws.append([r[k] for k in ["code","customer","phone","event","kategori","qty","total","order_date"]])
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width=min(32,max(14,max(len(str(c.value or "")) for c in col)+2))
            ws.freeze_panes="A2"; wb.save(path); messagebox.showinfo("Berhasil",f"Excel tersimpan:\\n{path}")
        except ImportError: messagebox.showerror("Modul belum ada","Jalankan: pip install -r requirements.txt")
        except Exception as e: messagebox.showerror("Ekspor gagal",str(e))

    def export_pdf(self):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")],initialfile="laporan_penjualan.pdf")
            if not path:return
            data=[["Kode","Pelanggan","Event","Kategori","Qty","Total","Tanggal"]]
            for r in self.report_data(): data.append([str(r["code"]),str(r["customer"]),str(r["event"]),str(r["kategori"]),str(r["qty"]),f'Rp {r["total"]:,.0f}',str(r["order_date"])])
            doc=SimpleDocTemplate(path,pagesize=landscape(A4),rightMargin=25,leftMargin=25,topMargin=30,bottomMargin=25)
            styles=getSampleStyleSheet(); story=[Paragraph("Laporan Penjualan Tiket Event",styles["Title"]),Spacer(1,15)]
            t=Table(data,repeatRows=1)
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),.4,colors.grey),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#EAF1F8")]),("FONTSIZE",(0,0),(-1,-1),8),("PADDING",(0,0),(-1,-1),6)]))
            story.append(t); doc.build(story); messagebox.showinfo("Berhasil",f"PDF tersimpan:\\n{path}")
        except ImportError: messagebox.showerror("Modul belum ada","Jalankan: pip install -r requirements.txt")
        except Exception as e: messagebox.showerror("Ekspor gagal",str(e))

    def backup(self):
        if self.db.mysql:
            messagebox.showinfo("MySQL","Untuk backup MySQL, gunakan Export > database melalui phpMyAdmin (menu Export).")
            return
        path=filedialog.asksaveasfilename(defaultextension=".db",filetypes=[("Database","*.db")],initialfile="backup_event_ticket.db")
        if path:
            self.db.cnx.commit(); shutil.copy2(DB_FILE,path); messagebox.showinfo("Backup","Backup database berhasil.")

if __name__ == "__main__":
    app=TicketApp()
    if app.winfo_exists(): app.mainloop()

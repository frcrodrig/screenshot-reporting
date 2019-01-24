#!/usr/bin/python
"""
Se realiza una captura de los dashboards de kibana/grafana y se guarda en formato PDF con un encabezado y un pie.
requerimientos:
    yum install python34-pip

    python3.6
    pip3 --proxy http://wwwwwwwwwwww
        selenium (3.141.0)
        Pillow (5.3.0)
    Firefox geckodriver
        https://github.com/mozilla/geckodriver/releases
        cp geckodriver /usr/local/bin/geckodriver


crontab
    0 13 * * * /usr/bin/python3 /opt/scripts/reportingdiego/reportes_captura.py
    

"""
#for capture
import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import Proxy, ProxyType
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from io import BytesIO

#for mail
import smtplib   
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def toma_captura(browser,page_width,page_height,titulo,subtitulo,url,asunto,espera,recorta, debug):
    """
    recibe info y guarda un pdf
        browser,
        page_width,
        page_height,
        titulo,
        subtitulo,
        url,
        asunto,
        espera,
        recorta
    """
    now = datetime.datetime.now()
    fecha = str(now.year)+"-"+str(now.month)+"-"+str(now.day)
    path="/opt/scripts/reportingdiego/pdf_generados/"
    fuente="/opt/scripts/reportingdiego/Oswald-Medium.ttf"

    font_titulo = ImageFont.truetype(fuente, 72)
    font_subtitulo = ImageFont.truetype(fuente, 42)
    font_titulo_reporte = ImageFont.truetype(fuente, 42)

    browser.set_window_size(page_width, page_height)
    browser.get(url)
    if debug:
        print("Se esta capturando la url: '{}' con asunto: '{}''".format(url, asunto))
    time.sleep(espera)

    js = 'return Math.max( document.body.scrollHeight, document.body.offsetHeight,  document.documentElement.clientHeight,  document.documentElement.scrollHeight,  document.documentElement.offsetHeight);'
    scrollheight = browser.execute_script(js)

    head_height = 222 # head.png
    foot_height = 146 # pie.png

    slices = []
    slices.append(Image.open("/opt/scripts/reportingdiego/head.png"))
    slices.append(Image.open(BytesIO(browser.get_screenshot_as_png())))
    slices.append(Image.open("/opt/scripts/reportingdiego/pie.png"))

    screenshot = Image.new('RGB', (slices[0].size[0], head_height+page_height+foot_height))
    offset = 0
    for img in slices:
        screenshot.paste(img, (0, offset))
        offset += img.size[1]

    if recorta:
        pdf_image = screenshot.crop((180, 0, page_width, head_height+page_height+foot_height))
    else:
        pdf_image = screenshot

    titulo_reporte=asunto+" - "+fecha
    draw = ImageDraw.Draw(pdf_image)
    draw.text((10, 0),titulo,(255,255,255),font=font_titulo)
    draw.text((13, 95),subtitulo,(255,255,255),font=font_subtitulo)
    draw.text((13, 145),titulo_reporte,(255,255,255),font=font_titulo_reporte)

    pdf_filename = asunto+"-"+fecha+".pdf"
    pdf_filename = pdf_filename.replace(" ", "_")
    pdf_image.save(path+pdf_filename, "PDF" ,resolution=100.0, save_all=True)
    # pdf_image.save(asunto+"-"+fecha+'.jpg')
    return(pdf_filename)

def enviomail(filename, asunto, fromaddr, toaddr, body, debug, borrarunavezenviado):
    """ envio mail """
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = asunto

    msg.attach(MIMEText(body, 'plain'))
    attachment = open("/opt/scripts/reportingdiego/pdf_generados/"+filename, "rb")
     
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
     
    msg.attach(part)
     
    server = smtplib.SMTP('10.*.*.*.*.*', 25)
    #server.starttls()
    #server.login(fromaddr, "YOUR PASSWORD")
    text = msg.as_string()
    
    if debug:
        print("Se envio por mail a ", toaddr)
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    
    if borrarunavezenviado:
        os.remove("/opt/scripts/reportingdiego/pdf_generados/"+filename)
        if debug:
            print("Se borra archivo recien enviado: '{}'".format(filename))

        

def main():
    """
    Inicializa el driver para capturar el firefox y llama para recibir las imagenes de las capturas de los dashboards
    """
    debug=True
    kibana=True
    grafana=True
    salemail=True
    borrarunavezenviado=True
    
    if debug:
        print("========= DEBUG ACTIVO ========= ")
        print("Genera reportes Kibana? ", kibana)
        print("Genera reportes Grafana? ", grafana)
        print("Envio mail?: ", salemail)
        print("Borro los pdf enviados? ", borrarunavezenviado)
        print("")


    #Agrego un proxy unicamente por la carga del mapa de grafana/kibana.
    myProxy = "wwwproxy:80"
    noProxy = ["localhost", "127.0.0.1"]

    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': myProxy,
        'ftpProxy': myProxy,
        'sslProxy': myProxy,
        'noProxy': noProxy # set this value as desired
        })

    #Conectar el driver
    caps = DesiredCapabilities.FIREFOX.copy()
    caps['acceptInsecureCerts'] = True
    os.environ['MOZ_HEADLESS'] = '1'
    proxy.add_to_capabilities(caps)
    browser = webdriver.Firefox(capabilities=caps)

    #Textos globales
    titulo="titulo"
    subtitulo="subtitulo"
    
    #Info mail
    remitente="reporte@kibana.ar"
    body = "Envio de reporte automatico"
    recipients = ['email@to.ar', 'email@t.ar']

    # ==========   DASHBOARDS KIBANA
    if kibana:
        urlbase="https://kibana:5601/app/kibana#/dashboard/"
        
        listadedashboards=[
        ["AWfCduai1kCPd7_KG749", "Kibana reporte 1"],
        ["AWfCduai1kCPd7_KG749", "Kibana reporte 2"],
        ["AWfCduai1kCPd7_KG749", "Kibana reporte 3"]]

        for dashboard in listadedashboards:
            pdf_filename=toma_captura(browser, 1900, 1720, titulo, subtitulo, urlbase+dashboard[0], dashboard[1], 120, True, debug)
            if debug:
                print("Se guardo el pdf: ", pdf_filename)
            if salemail:
                asuntomail="Reporte de "+dashboard[1]
                enviomail(pdf_filename, asuntomail, remitente, recipients, body, debug, borrarunavezenviado)


    # ==========   DASHBOARDS GRAFANA
    
    if grafana:
        urlbase="http://grafana:3000/d/"
        
        listadedashboards=[
        ["uri dashboard, "Titulo Reporte Grafana"],
        ["uri dashboard, "Titulo Reporte Grafana"],]

        urlparametros="?orgId=1&from=now-24h&to=now&theme=light"
        browser.get("http://grafana:3000/login")
        username = browser.find_element_by_name("username")
        password = browser.find_element_by_name("password")
        username.send_keys("username")
        password.send_keys("password")

        from selenium.webdriver.common.keys import Keys
        password.send_keys(Keys.ENTER)

        for dashboard in listadedashboards:
            pdf_filename=toma_captura(browser, 1900, 3000, titulo, subtitulo, urlbase+dashboard[0]+urlparametros, dashboard[1], 25, False, debug)
            if debug:
                print("Se guardo el pdf: ", pdf_filename)
            if salemail:
                asuntomail="Reporte de "+dashboard[1]
                enviomail(pdf_filename, asuntomail, remitente, recipients, body, debug, borrarunavezenviado)
    
    #Cierro el browser
    browser.quit()


main()

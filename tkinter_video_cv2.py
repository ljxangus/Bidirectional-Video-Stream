from Tkinter import *
#import ImageTk, Image, numpy, math, time, socket, sys, errno, tkFileDialog, threading, socket
import os, glob, threading, socket, time, numpy
import cv2
import cv2.cv as cv
from PIL import Image, ImageTk
from optparse import OptionParser

running_flag_send = True
running_flag_receive = True
click_before = False
receive_before = False
receive_not_stop = False
send_not_stop = False

class Client:
    """Client is used to send Video stream to server"""
    def __init__(self,server_host="localhost",port=6123,framesize=(160,120),fps=10):
        self.server_host = server_host
        self.port = port
        self.framesize = framesize
        self.fps = fps
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_frame_num = 0
        self.send_speed = 0
        self.send_size = (160,120)
        self.compression_rate = 20

    def prepare_video(self,server_host="localhost",port=6123,send_size_x=160,send_size_y=120,send_fps=10,compress_rate=20):
        #cv.StartWindowThread()
        #cv.NamedWindow("Client", cv.CV_WINDOW_AUTOSIZE)
        self.server_host = server_host
        self.port = port
        self.send_size = (send_size_x,send_size_y)
        self.fps = send_fps
        self.compression_rate = compress_rate
        self.capture = cv2.VideoCapture(0)
        global click_before,send_not_stop
        click_before = True
        send_not_stop = True

    def connect(self):
        global stop_flag
        while stop_flag:
            #set the framesize in the client side, size only for showing locally
            frame = self.get_frame(window_size=(640,480))
            
            #set the fps
            time.sleep(1/self.fps)

            self.send_frame(frame)

    def get_frame(self,resize_size=None,window_size=None):
        #Get the capture and return it to the client
        success, frame = self.capture.read()

        if not success:
            return

        if resize_size is None:
            resize_size = self.send_size
        if window_size is None:
            window_size=self.framesize

        resize_image = cv2.resize(frame,resize_size)
        #cv.Resize(frame,resize_image)

        window_size_image = cv2.resize(frame,window_size)
        #cv.Resize(frame,window_size_image)
        jpegImg_window = window_size_image #Image.fromstring("RGB",cv.GetSize(window_size_image),window_size_image.tostring())
        #cv.ShowImage("Client",window_size_image)     

        #jpegImg = Image.fromstring("RGB",cv.GetSize(resize_image),resize_image.tostring())
        #here jpegImg is a PIL instance
        #retStr = jpegImg.tostring("jpeg","RGB")
        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),self.compression_rate]
        ret, data = cv2.imencode('.jpg', resize_image, encode_param)
        #set the fps
        #time.sleep(1/self.fps)
        return data,jpegImg_window

    def send_frame(self,frame):
        data = numpy.array(frame)
        frame = data.tostring()

        self.sock.sendto(frame,(self.server_host,self.port))
        self.send_speed = self.send_speed + len(frame)
        self.send_frame_num = self.send_frame_num + 1
        if self.send_frame_num % self.fps == 0:
            #print "Transmission Speed:",self.send_speed/1000," KBytes/s"
            self.send_speed = 0


class Server:
    """Server is used to receive Video stream from client"""
    def __init__(self,client_host="",port=6124,framesize=(160,120)):
        self.client_host = client_host
        self.port = port
        self.framesize = framesize
        self.sock = None #socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.sock.bind((self.client_host,self.port))
        self.buffer_size = 65536
        print "UDPServer begins receiving frame"
        #cv.StartWindowThread()
        #cv.NamedWindow("Server", cv.CV_WINDOW_AUTOSIZE)

    def receiving(self):
        global running_flag_receive
        while running_flag_receive:
            frame = self.receive_frame()
            decimg = cv2.imdecode(frame,1)
            #self.set_frame(frame,resize_size=(640,480))

    def set_frame(self,frame,resize_size=None):
        jpegPIL = Image.fromstring("RGB",self.framesize,frame,"jpeg","RGB","raw")
        temp_img = cv.CreateImage(self.framesize,cv.IPL_DEPTH_8U,3)
        cv.SetData(temp_img,jpegPIL.tostring())

        #resize operation
        if resize_size is None:
            resize_size = self.framesize
        resize_image = cv.CreateImage(resize_size,cv.IPL_DEPTH_8U,3)
        cv.Resize(temp_img,resize_image)

        #cv.ShowImage("Server",resize_image)
    def socket_prepared(self,receive_port=6124):
        #if self.sock is not None:
        #    self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.client_host,receive_port))
        global receive_before,receive_not_stop
        receive_before = True
        receive_not_stop = True

    def receive_frame(self):
        chunk, addr = self.sock.recvfrom(self.buffer_size)
        #print "Frame receive with Compressed Size = ",len(chunk)
        return numpy.fromstring(chunk, dtype='uint8')
        #return ''.join(chunk)

class ImageGUI(Frame):
    def __init__(self, parent):
        self.parser = OptionParser()
        #self.parser.add_option("-i", "--img_url", type="str", default="bg.jpg", help="imgurl")
        self.parser.add_option("-d", "--dir_url", type="str", default="/img_data", help="dirurl")
        self.parser.add_option("-s", "--send_port", type="int", default=6123, help="sendport")
        self.parser.add_option("-r", "--receive_port", type="int", default=6124, help="receiveport")
        self.parser.add_option("-i", "--send_ip", type="str", default="127.0.0.1", help="sendip")
        self.parser.add_option("-e", "--self_ip", type="str", default="127.0.0.1", help="selfip")
        self.parser.add_option("-x", "--window_size_x",type="int", default=640, help="windowsizex")
        self.parser.add_option("-y", "--window_size_y",type="int", default=480, help="windowsizey")
        self.parser.add_option("-a", "--send_size_x",type="int", default=160, help="sendsizex")
        self.parser.add_option("-b", "--send_size_y",type="int", default=120, help="sendsizey")
        self.parser.add_option("-f", "--fps",type="int", default=10, help="fps")
        self.parser.add_option("-c", "--compress_rate",type="int", default=20, help="compress_rate")
        (self.options, self.args) = self.parser.parse_args()

        self.ip = self.options.self_ip

        self.dirPath = os.getcwd()+self.options.dir_url
        self.send_port = self.options.send_port
        self.send_ip = self.options.send_ip
        self.receive_port = self.options.receive_port 
        self.window_size_x = self.options.window_size_x
        self.window_size_y = self.options.window_size_y
        self.send_size_x = self.options.send_size_x
        self.send_size_y = self.options.send_size_y
        self.fps = self.options.fps
        self.compress_rate = self.options.compress_rate

        self.sendPacketValue = StringVar()
        self.sendByteValue = StringVar()
        self.receivePacketValue = StringVar()
        self.receiveByteValue = StringVar()

        self.socket = None

        Frame.__init__(self, parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        #client side
        self.parent.title("Video Stream")
        self.pack(fill=BOTH, expand=1)

        self.labelPort2 = Label(self, text="receive port number")
        self.labelPort2.place(x=510,y=0.5)

        self.portText2 = Text(self, width = 10, height = 1)
        self.portText2.place(x=510,y=20)
        self.portText2.insert(END, str(self.receive_port))

        self.receiveButton = Button(self, text="Start to Receive", width = 15, height = 1, command=self.onReceiveClick)
        self.receiveButton.place(x=550,y=450)

        self.receiveStopButton = Button(self, text="Stop Receiving", width=15,height=1,command=self.onStopReceivingClick)
        self.receiveStopButton.place(x=750,y=450)

        self.sendPacketLabel = Label(self, text="Frame Sent:")
        self.sendPacketLabel.place(x=750,y=0.5)
        self.sendPacket = Label(self, textvariable=self.sendPacketValue)
        self.sendPacket.place(x=900,y=0.5)

        self.sendByteLabel = Label(self, text="Data Speed:")
        self.sendByteLabel.place(x=750,y=20)
        self.sendByte = Label(self, textvariable=self.sendByteValue)
        self.sendByte.place(x=900,y=20)

        self.receivePacketLabel = Label(self, text="Frame received:")
        self.receivePacketLabel.place(x=750,y=40.5)
        self.receivePacket = Label(self, textvariable=self.receivePacketValue)
        self.receivePacket.place(x=900,y=40.5)

        self.receiveByteLabel = Label(self, text="Data received:")
        self.receiveByteLabel.place(x=750,y=62)
        self.receiveByte = Label(self, textvariable=self.receiveByteValue)
        self.receiveByte.place(x=900,y=62)

        '''
        self.timeLabel = Label(self, text="Elapsed time:")
        self.timeLabel.place(x=750,y=40)
        self.time = Label(self, textvariable=self.elapsedTimeValue)
        self.time.place(x=900,y=40)

        self.rateLabel = Label(self, text="Rate:")
        self.rateLabel.place(x=750,y=60)
        self.rate = Label(self, textvariable=self.averageRateValue)
        self.rate.place(x=900,y=60)
        '''

        self.sender = Client()
        self.receiver = Server()
        
        #sending window initialization
        self.initialImage = Image.open("videochat.jpg")
        tkimage = ImageTk.PhotoImage(self.initialImage)
        self.imgLabel = Label(self,image=tkimage)
        self.imgLabel.image = tkimage
        self.imgLabel.place(x=10,y=100)

        #receiving window initialization
        tkimage2 = ImageTk.PhotoImage(self.initialImage)
        self.imgLabel2 = Label(self,image=tkimage2)
        self.imgLabel2.image = tkimage2
        self.imgLabel2.place(x=600,y=100)

        #server side
        
        self.labelPort = Label(self, text="send port number")
        self.labelPort.place(x=10,y=0.5)

        self.portText = Text(self, width = 10, height = 1)
        self.portText.place(x=10,y=20)
        self.portText.insert(END, str(self.send_port))

        self.labelframe = Label(self, text="send frame size")
        self.labelframe.place(x=200,y=0.5)

        self.labelfps = Label(self, text="send frame FPS")
        self.labelfps.place(x=200,y=40.5)
        self.fpsText = Text(self, width = 10, height = 1)
        self.fpsText.place(x =200,y=60)
        self.fpsText.insert(END, str(self.fps))

        self.labelcom_rate = Label(self, text="Compression Rate")
        self.labelcom_rate.place(x=300,y=40.5)
        self.com_rateText = Text(self, width = 10, height = 1)
        self.com_rateText.place(x =300,y=60)
        self.com_rateText.insert(END, str(self.compress_rate))

        self.frameXText = Text(self, width = 10, height = 1)
        self.frameXText.place(x=200,y=20)
        self.frameXText.insert(END, str(self.send_size_x))
        self.frameYText = Text(self, width = 10, height = 1)
        self.frameYText.place(x=300,y=20)
        self.frameYText.insert(END, str(self.send_size_y))

        self.labelIP = Label(self, text="send ip address")
        self.labelIP.place(x=10,y=40.5)

        self.ipText = Text(self, width = 15, height = 1)
        self.ipText.place(x=10,y=60)
        self.ipText.insert(END, str(self.send_ip))
        
        self.buttonSend = Button(self, text="Start to Send", width=10, height=1, command=self.onSendClick)
        self.buttonSend.place(x=80,y=450)

        self.buttonStopSending = Button(self, text="Stop sending", width=10, height=1, command=self.onStopSendingClick)
        self.buttonStopSending.place(x=220,y=450)

    def onSendClick(self):
        print "onSendClick"
        global click_before,send_not_stop
        if send_not_stop:
            print "Sender Not Yet Stop!"
            return
        if not click_before:
            ip = str(self.ipText.get("0.0",END))
            port = int(str(self.portText.get("0.0",END)))
            send_frame_x = int(str(self.frameXText.get("0.0",END)))
            send_frame_y = int(str(self.frameYText.get("0.0",END)))
            frame_fps = int(str(self.fpsText.get("0.0",END)))
            compress_rate = int(str(self.com_rateText.get("0.0",END)))
            #print "\n port is ",port
            #print "\n ip is",ip
            self.sender.prepare_video(server_host=ip,port=port,send_size_x=send_frame_x,send_size_y= send_frame_y,send_fps= frame_fps)
        #print "\n sender port is ",self.sender.port
        #print "\n sender ip is",self.sender.server_host
        pSend = threading.Thread(target=self.draw_cam_frame)
        pSend.start()

    def onReceiveClick(self):
        print "onReceiveClick"
        global receive_before,receive_not_stop
        port = int(str(self.portText2.get("0.0",END)))
        #print "\n port is ",port
        if receive_not_stop:
            print "Receiver Not Yet Stop!"
            return
        if not (self.receiver.port == port and receive_before):
            self.receiver.socket_prepared(receive_port=port)
        #print "\n receiver port is ",self.receiver.port
        pRece = threading.Thread(target=self.draw_receive_frame)
        pRece.start()


    def draw_cam_frame(self):
        global running_flag_send
        running_flag_send = True
        count = 0
        while running_flag_send:
            str_img,frame = self.sender.get_frame(window_size=(320,240))
            im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            new_frame = Image.fromarray(im)
            img = ImageTk.PhotoImage(new_frame)
            self.imgLabel.configure(image=img)
            self.imgLabel.image = img
            count = count + 1
            #print count
            if count % self.sender.fps == 0:
                count = 0
                self.sendByteValue.set(str(self.sender.send_speed/1000)+" KBytes")
            self.sendPacketValue.set(str(self.sender.send_frame_num)+" Frames")
            self.update()
            self.sender.send_frame(str_img)
            time.sleep(1/self.sender.fps)

    def draw_receive_frame(self):
        global running_flag_receive
        running_flag_receive = True
        while running_flag_receive:
            frame = self.receiver.receive_frame()
            decimg = cv2.imdecode(frame,1)
            im = cv2.cvtColor(decimg, cv2.COLOR_BGR2RGB)
            temp_frame = Image.fromarray(im)
            #temp_frame = Image.fromstring("RGB",self.receiver.framesize,frame,"jpeg","RGB","raw")
            temp_frame = ImageTk.PhotoImage(temp_frame)
            self.imgLabel2.configure(image=temp_frame)
            self.imgLabel2.image = temp_frame
            self.update()

    def onStopSendingClick(self):
        print "OnClickStopSending"
        global running_flag_send,send_not_stop
        send_not_stop = False
        running_flag_send = False
        global running_flag_receive,receive_not_stop
        running_flag_receive = False
        receive_not_stop = False

    def onStopReceivingClick(self):
        print "OnClickStopReceiving"
        global running_flag_receive,receive_not_stop
        running_flag_receive = False
        receive_not_stop = False
        #self.receiver.sock.close()


def main():
    root = Tk()
    root.geometry("1000x500+300+300")
    app = ImageGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
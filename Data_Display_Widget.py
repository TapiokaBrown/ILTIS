# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 13:10:05 2015

@author: georg
"""
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import weakref
import scipy as sp
from scipy import random

class Data_Display_Widget(QtGui.QWidget):
    def __init__(self,Main,parent):
        super(Data_Display_Widget,self).__init__()

        self.Main = Main
        self.Main.Data_Display = self
        self.MainWindow = parent
        
        self.Frame_Visualizer = None
        self.LUT_Controlers = None
        self.Traces_Visualizer = None
        
        self.color_maps = None
        self.colors = None
        
        ### colormaps
        pos = sp.array([1,0.66,0.33,0])
        cols = sp.array([[255,255,255,255],[255,220,0,255],[185,0,0,255],[0,0,0,0]],dtype=sp.ubyte)
        self.heatmap = pg.ColorMap(pos,cols)
        
        pos = sp.array([1,0])
        cols = sp.array([[255,255,255,255],[0,0,0,255]],dtype=sp.ubyte)
        self.graymap = pg.ColorMap(pos,cols)
        
        self.initUI()
        pass
        
    def initUI(self):
        # ini the widgets
        self.Frame_Visualizer = Frame_Visualizer_Widget(self.Main,self)
        self.LUT_Controlers = LUT_Controlers_Widget(self.Main,self)
        self.Traces_Visualizer = Traces_Visualizer_Widget(self.Main,self)
        
        # color ### FIXME does not work ... 
        palette = QtGui.QPalette(QtGui.QColor(90,90,90,90))
        self.setPalette(palette)
        
        ### layout
        # The main Layout: Stacks Frame_Visualizer (+ LUT_Controlers) and Traces_Visualizer
        self.Container = QtGui.QHBoxLayout(self) 

        
        # Frame_Visualizer + LUT_Controlers 
        self.FrameLayout = QtGui.QHBoxLayout() 
        self.FrameLayout.addWidget(self.Frame_Visualizer)
        self.FrameLayout.addWidget(self.LUT_Controlers)
        self.FrameLayout.setStretchFactor(self.Frame_Visualizer,5)
        self.FrameLayout.setStretchFactor(self.LUT_Controlers,1)

        # Frame_Visualizer and Traces_Visualizer divided by QSplitter
        self.FrameContainer = QtGui.QWidget() # is needed because Splitter works on Widgets and not on layouts
        self.FrameContainer.setLayout(self.FrameLayout) # putting the widgets inside
        self.DisplaySplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        
        # putting both in
        self.DisplaySplitter.addWidget(self.FrameContainer)
        self.DisplaySplitter.addWidget(self.Traces_Visualizer)
        
        # setting initial split

        # and putting all in the main container
        self.Container.addWidget(self.DisplaySplitter)
        self.setLayout(self.Container)


    def reset(self):
        self.Frame_Visualizer.reset()
        self.LUT_Controlers.reset()
        self.Traces_Visualizer.reset()
        pass
    
    def init_data(self):
        # weakref to data
        self.data = weakref.ref(self.Main.Data)()
        self.Options = weakref.ref(self.Main.Options)()
        
        self.colors,self.color_maps = self.calc_colormaps(self.data.nFiles)
        self.Frame_Visualizer.init_data()
        self.LUT_Controlers.init_data()
        self.Traces_Visualizer.init_data()
        self.Frame_Visualizer.update()
        pass
    
    def update(self):
        self.Frame_Visualizer.update()
        self.Traces_Visualizer.update()
    
    def calc_colormaps(self,nColors,hot=False):
        """ generate evenly spaced colors on the HSV wheel """
        h = sp.linspace(0,360,nColors,endpoint=False).astype('int').tolist()
        s = [255] * nColors
        v = [255] * nColors
        color_maps = []
        colors = []
        for n in range(nColors):
            Color = QtGui.QColor()
            Color.setHsv(h[n],s[n],v[n])
            rgb = Color.getRgb()
            if hot == False:
                pos = sp.array([1,0])
                cols = sp.array([rgb,[0,0,0,0]],dtype=sp.ubyte)
                cmap = pg.ColorMap(pos,cols)
                colors.append(rgb)
                color_maps.append(cmap)
                pass
            if hot == True:
                pos = sp.array([1,0.8,0])
                cols = sp.array([[255,255,255,255],rgb,[0,0,0,255]],dtype=sp.ubyte)
                cmap = pg.ColorMap(pos,cols)
                colors.append(rgb)
                color_maps.append(cmap)
                pass
            pass
        return colors, color_maps
    
    pass

class Frame_Visualizer_Widget(pg.GraphicsView):
    """ 
    missing: intercept mouse click and add ROI
    
    """
    def __init__(self,Main,parent):
        super(Frame_Visualizer_Widget,self).__init__()
        
        self.Main = Main
        self.Main.Frame_Visualizer = self
        
        self.Data_Display = parent
        
        self.ImageItems = [] # list with the image items
        self.ImageItems_dFF = [] # list with the image items
        self.frame = 0
        
        self.ViewBox = pg.ViewBox()
        self.ViewBox.setAspectLocked()
        self.ViewBox.setAcceptDrops(True)
        self.setCentralItem(self.ViewBox)
        
        # mouse interaction
        self.scene().sigMouseClicked.connect(self.mouseClicked)
        
        # weakrefs to data object and Options object

        pass

    def update(self):
        """ former set image data."""
        """ 
        has to check: -is average? -is dFF? -flag to show? -only one?
       
        average behaviour: take all that are active, average and overlay
        
        dFF behaviour: if multiple channels are active, the dFF are over
        layed and colored according to their channel

        if only one channel is active:        
        raw is in grayscale, dFF is in glow color map
        """
        ### for implementation of global lut mod
#        current_lut = self.LUTwidgets.currentIndex()

        # work only on those that are active
        for n in range(self.data.nFiles):
            if self.Options.view['show_flags'][n] == False: # hide inactive
                self.ImageItems[n].hide()
                self.ImageItems_dFF[n].hide()

                
            if self.Options.view['show_flags'][n] == True: # work only on those that are active
                
                if self.Options.view['show_dFF']: # when showing dFF
                
                    if self.Options.view['show_monochrome']: # when in mono glow mode
                        self.ImageItems[n].show()
                    else:
                        self.ImageItems[n].hide()
                        
                    if self.Options.view['show_avg']: # when showing avg
                        self.ImageItems_dFF[n].setImage(sp.average(self.data.dFF[:,:,:,n],axis=2))
                        self.ImageItems[n].setImage(sp.average(self.data.raw[:,:,:,n],axis=2))

                    else: 
                        self.ImageItems_dFF[n].setImage(self.data.dFF[:,:,self.frame,n])
                        self.ImageItems[n].setImage(self.data.raw[:,:,self.frame,n])


                    self.ImageItems_dFF[n].show()
                    
                else: # when showing raw
                    self.ImageItems_dFF[n].hide() # no dFF
                    if self.Options.view['show_avg']:
                        self.ImageItems[n].setImage(sp.average(self.data.raw[:,:,:,n],axis=2))
                    else:
                        self.ImageItems[n].setImage(self.data.raw[:,:,self.frame,n])
                        
                    self.ImageItems[n].show()
                    
                self.ImageItems[n].setLevels(self.Data_Display.LUT_Controlers.raw_levels[n])
                self.ImageItems_dFF[n].setLevels(self.Data_Display.LUT_Controlers.dFF_levels[n])        
        pass
    
    def init_data(self):
        ### initializing image and LUTwidget
        self.data = weakref.ref(self.Main.Data)()
        self.Options = weakref.ref(self.Main.Options)()

        for n in range(self.data.nFiles):
            ImageItem_raw = pg.ImageItem(self.data.raw[:,:,self.frame,n])
            self.ViewBox.addItem(ImageItem_raw)
            self.ImageItems.append(ImageItem_raw)
            
            ImageItem_dFF = pg.ImageItem(self.data.dFF[:,:,self.frame,n])
            self.ViewBox.addItem(ImageItem_dFF)
            self.ImageItems_dFF.append(ImageItem_dFF)
        
        self.ViewBox.autoRange()
        self.set_composition_mode(12)
#        self.update()
        
        pass
        
    def set_composition_mode(self,n):
        """ set the composition mode for different blending properties """
        for ImageItem in self.ImageItems:
            ImageItem.setCompositionMode(n)
            
        for ImageItem in self.ImageItems_dFF:
            ImageItem.setCompositionMode(n)              
        
    def reset(self):
        ### clearing the GUI if it has been initialized before
        for item in self.ImageItems:
            self.ViewBox.removeItem(item)
        self.ImageItems = []
        for item in self.ImageItems_dFF:
            self.ViewBox.removeItem(item)
        self.ImageItems_dFF = []
        pass
    
    def mouseClicked(self, evt):
        """ for ROI placement
        add functionality: watch for ROI placing toggle/switch        
        """
        if pg.graphicsItems.ViewBox.ViewBox == type(evt.currentItem): # this is the fix for the ROI in the corners bug
            if evt.button() == 1:
                pos = self.ViewBox.mapToView(evt.pos()) # position of mouse click
                self.Main.ROIs.add_ROI(pos=sp.array([pos.x(),pos.y()]))
                self.Data_Display.update()
                pass
            pass
        pass
    
    pass


class LUT_Controlers_Widget(QtGui.QWidget):
    def __init__(self,Main,parent):
        super(LUT_Controlers_Widget,self).__init__()
        
        self.Main = Main
        self.Main.LUT_Controlers = self
        
        self.Data_Display = parent
        self.LUTwidgets = QtGui.QStackedWidget()
        self.LUTwidgets_dFF = QtGui.QStackedWidget()

        self.raw_levels = []
        self.dFF_levels = []
        
        # layout
        self.Layout = QtGui.QHBoxLayout()
        self.Layout.addWidget(self.LUTwidgets)
        self.Layout.addWidget(self.LUTwidgets_dFF)
        self.setLayout(self.Layout)
        pass
    
    def init_data(self):
        # get weakref to dataset
        self.data = weakref.ref(self.Data_Display.MainWindow.Main.Data)()
        self.Options = weakref.ref(self.Data_Display.MainWindow.Main.Options)()
        
        # ini and connect
        for n in range(self.data.nFiles):
            # for raw
            self.raw_levels.append(self.calc_levels(self.data.raw[:,:,:,n],fraction=(0.3,0.9995),nbins=100,samples=2000))
            LUTwidget = pg.HistogramLUTWidget()
            LUTwidget.setImageItem(self.Data_Display.Frame_Visualizer.ImageItems[n])
            LUTwidget.item.setHistogramRange(self.data.raw.min(),self.data.raw.max()) # disables autoscaling
            LUTwidget.item.setLevels(self.raw_levels[n][0],self.raw_levels[n][1])
            LUTwidget.item.gradient.setColorMap(self.Data_Display.color_maps[n])
            self.LUTwidgets.addWidget(LUTwidget)
    
            # for dFF        
            self.dFF_levels.append(self.calc_levels(self.data.dFF[:,:,:,n],fraction=(0.7,0.9995),nbins=100,samples=2000))
            LUTwidget = pg.HistogramLUTWidget()
            LUTwidget.setImageItem(self.Data_Display.Frame_Visualizer.ImageItems_dFF[n])
            LUTwidget.item.setHistogramRange(self.data.dFF.min(),self.data.dFF.max()) # disables autoscaling
            LUTwidget.item.setLevels(self.dFF_levels[n][0],self.dFF_levels[n][1])
            LUTwidget.item.gradient.setColorMap(self.Data_Display.color_maps[n])
            self.LUTwidgets_dFF.addWidget(LUTwidget)
            pass
        
        for n in range(self.data.nFiles):
            self.LUTwidgets.widget(n).item.sigLevelsChanged.connect(self.LUT_changed)
            self.LUTwidgets_dFF.widget(n).item.sigLevelsChanged.connect(self.LUT_changed)
            pass
        pass
    
    def LUT_changed(self):
        if self.Options.view['use_global_levels']:
            # take LUT levels from active LUT widget and write it to all
            current_lut = self.LUTwidgets.currentIndex()
            for n in range(self.data.nFiles):
                levels = self.LUTwidgets.widget(current_lut).item.getLevels()
                self.raw_levels[n] = levels
                self.LUTwidgets.widget(n).item.setLevels(levels[0],levels[1])
                
                dFF_levels = self.LUTwidgets_dFF.widget(current_lut).item.getLevels()
                self.dFF_levels[n] = dFF_levels
                self.LUTwidgets_dFF.widget(n).item.setLevels(dFF_levels[0],dFF_levels[1])
                
        else:
            for n in range(self.data.nFiles):
                levels = self.LUTwidgets.widget(n).item.getLevels()
                self.raw_levels[n] = levels
                self.LUTwidgets.widget(n).item.setLevels(levels[0],levels[1])
                
                dFF_levels = self.LUTwidgets_dFF.widget(n).item.getLevels()
                self.dFF_levels[n] = dFF_levels
                self.LUTwidgets_dFF.widget(n).item.setLevels(dFF_levels[0],dFF_levels[1])
                
        self.update()
        pass
        
    def calc_levels(self,data,fraction=(0.1,0.9),nbins=100,samples=None):
        """ fraction is a tuple with (low, high) in the range of 0 to 1 
        nbins is the number of bins for the histogram resolution

        if samples: draw this number of samples (random inds) for faster
        calculation
        """
        if samples:
#            data = data.flatten()[random.permutation(sp.arange(sp.prod(data.shape)))[:samples]]
            data = data.flatten()[random.randint(sp.prod(data.shape),size=samples)]
        else:
            data = data.flatten()
        y,x = sp.histogram(data,bins=nbins)
        cy = sp.cumsum(y).astype('float32')
        cy = cy / cy.max()
        minInd = sp.argmin(sp.absolute(cy - fraction[0]))
        maxInd = sp.argmin(sp.absolute(cy - fraction[1]))
        levels = (x[minInd],x[maxInd])
        return levels
        
    def reset_levels(self,which='dFF'):
        """ (re)calculate levels and set them """
        for n in range(self.Main.Data.nFiles):
            if which == 'dFF':
                levels = self.calc_levels(self.data.dFF[:,:,:,n],fraction=(0.7,0.9995),nbins=100,samples=2000)
                self.dFF_levels[n] = levels
                self.LUTwidgets_dFF.widget(n).item.setLevels(levels[0],levels[1])
                pass
            
            if which == 'raw':
                levels = self.calc_levels(self.data.raw[:,:,:,n],fraction=(0.3,0.9995),nbins=100,samples=2000)
                self.dFF_levels[n] = levels
                self.LUTwidgets_dFF.widget(n).item.setLevels(levels[0],levels[1])                
                pass

        
        
    def reset(self):
        """ reset function """
        self.raw_levels = []
        self.dFF_levels = []
        for n in range(self.LUTwidgets.count()):
            self.LUTwidgets.removeWidget(self.LUTwidgets.widget(0))
            self.LUTwidgets_dFF.removeWidget(self.LUTwidgets_dFF.widget(0))
        pass
    pass
#
#        
#
class Traces_Visualizer_Widget(pg.GraphicsLayoutWidget):
    def __init__(self,Main,parent):
        super(Traces_Visualizer_Widget,self).__init__()
        
        self.Main = Main
        self.Main.Traces_Visualizer = self        
        
        self.Data_Display = parent
        self.plotWidget = pg.GraphicsLayoutWidget()
        
        self.plotItem = self.addPlot()
        self.plotItem.setLabel('left','F')
        self.plotItem.setLabel('bottom','frame #')
        self.plotItem.showGrid(x=True,y=True,alpha=0.5)
        
        self.traces = []

        
        self.vline = self.plotItem.addLine(x=self.Data_Display.Frame_Visualizer.frame,movable=True)
        self.vline.sigPositionChanged.connect(self.vlinePosChanged) # add interactivity
    
    def init_data(self):
        
        self.Options = weakref.ref(self.Main.Options)()
        
        ### plot
        self.vline.setBounds((0, self.Main.Data.nFrames -1))

        for n in range(self.Main.Data.nFiles):
            pen = pg.mkPen(self.Data_Display.colors[n], width=2)
            trace = self.plotItem.plot(pen=pen)
            self.traces.append(trace)
            
        self.plotItem.setRange(xRange=[0, self.Main.Data.nFrames], disableAutoRange=False)
        
        self.stim_region = pg.LinearRegionItem(values=[self.Options.preprocessing['stimulus_onset'], self.Options.preprocessing['stimulus_offset']],movable=False,brush=pg.mkBrush([50,50,50,100]))
        for line in self.stim_region.lines:
            line.hide()
        self.stim_region.setZValue(-1000)
        self.plotItem.addItem(self.stim_region)
        pass
    
    def vlinePosChanged(self,evt):
        """ updater for the zlayer change caused by the vline """
        self.Data_Display.Frame_Visualizer.frame = int(evt.pos().x())
        self.vline.setValue(evt.pos().x())
        self.Data_Display.Frame_Visualizer.update()
        pass        
        
    def update(self):
#        self.last_pos = pos # needed for keeping the lines while some are removed or added
        if self.Main.ROIs.nROIs != 0:
                
            for n in range(self.Main.Data.nFiles):
                if self.Options.view['show_flags'][n] == True: # only work on active datasets
                
                    # implementation using the pyqtgraph internal slicing
                    ROI = self.Main.ROIs.ROI_list[self.Main.ROIs.active_ROI_id]
                    
                    # func bool mask slicing
                    mask, inds = self.Main.ROIs.get_ROI_mask(ROI)
                    if self.Options.view['show_dFF']:
                        sliced = self.Main.Data.dFF[mask,:,n]
                    else:
                        sliced = self.Main.Data.raw[mask,:,n]
    
                    Trace = sp.average(sliced,axis=0)
                    self.traces[n].setData(Trace)
                    self.traces[n].show()
                    
                    # update the normal traces plot or update the Trace Inspector.
                    # this needs cleaning!
    #                if self.Traces_Inspector_exists_flag:
    #                    self.Traces_Inspector.update_trace(Trace,n)
    #                    self.Traces_Inspector.traces[n].show()
    #                else:
    
                else:
                    self.traces[n].hide()
    #                if self.Traces_Inspector_exists_flag:
    #                    self.Traces_Inspector.traces[n].hide()
    #                self.dots[n].hide()
                pass
            pass
    
    def reset(self):
        for trace in self.traces:
            trace.clear()
        self.traces = []
        
        pass
    pass

if __name__ == '__main__':
    pass
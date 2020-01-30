from matplotlib.widgets import Slider
from matplotlib import pyplot as plt
import numpy as np

class Interactive:
    def __init__(self):
        pass

    def update(self, val):
        global xmarkers, ymarkers
        for i in np.arange(N):
            ymarkers[i] = sliders[i].val 
        axes.set_ydata(ymarkers) # update values on the plot
        axes.set_xdata(xmarkers)
        fig.canvas.draw_idle() # redraw canvas while idle

    def button_press_callback(self, event, xmarkers, ymarkers, axes, epsilon):
        'whenever a mouse button is pressed'
        global pind
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        pind = self.get_ind_under_point(event, xmarkers, ymarkers, axes, epsilon)    

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        global pind
        if event.button != 1:
            return
        pind = None

    def get_ind_under_point(self, event, xmarkers, ymarkers, axes, epsilon):
        'get the index of the marker under the cursor if within epsilon tolerance'

        t = axes.transData.inverted()
        tinv = axes.transData 
        xy = t.transform([event.x,event.y])
        xr = np.reshape(xmarkers,(np.shape(xmarkers)[0],1))
        yr = np.reshape(ymarkers,(np.shape(ymarkers)[0],1))
        xy_vals = np.append(xr,yr,1)
        xyt = tinv.transform(xy_vals)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        ind = indseq[0]

        if d[ind] >= epsilon:
            ind = None

        return ind

    def motion_notify_callback(self, event):
        'on mouse movement'
#        global xfunc, yfunc, xmarkers, ymarkers, sliders
        global pind
        if pind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        g = np.hypot(xfunc-event.xdata, yfunc-event.ydata)
        indsequence, = np.nonzero(g == g.min())
        ind = indsequence[0]
        ymarkers[pind] = yfunc[ind]
        xmarkers[pind] = xfunc[ind]

        sliders[pind].set_val(ymarkers[pind]) # update curve via sliders and draw
        fig.canvas.draw_idle()

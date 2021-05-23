from pyqtgraph.Qt import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class LaserWidget(Widget):
    """ Laser widget for setting laser powers etc. """

    sigEnableChanged = QtCore.Signal(str, bool)  # (laserName, enabled)
    sigValueChanged = QtCore.Signal(str, float)  # (laserName, value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laserModules = {}

        self.scrollContainer = QtWidgets.QGridLayout()
        self.scrollContainer.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.scrollContainer)

        self.grid = QtWidgets.QGridLayout()

        self.gridContainer = QtWidgets.QWidget()
        self.gridContainer.setLayout(self.grid)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidget(self.gridContainer)
        self.scrollArea.setWidgetResizable(True)
        self.scrollContainer.addWidget(self.scrollArea)
        self.gridContainer.installEventFilter(self)

    def addLaser(self, laserName, valueUnits, wavelength, valueRange=None, valueRangeStep=1):
        """ Adds a laser module widget. valueRange is either a tuple
        (min, max), or None (if the laser can only be turned on/off). """

        control = LaserModule(
            name=laserName, units=valueUnits, wavelength=wavelength,
            valueRange=valueRange, tickInterval=5, singleStep=valueRangeStep,
            initialPower=valueRange[0] if valueRange is not None else 0
        )
        control.sigEnableChanged.connect(
            lambda enabled: self.sigEnableChanged.emit(laserName, enabled)
        )
        control.sigValueChanged.connect(
            lambda value: self.sigValueChanged.emit(laserName, value)
        )

        nameLabel = QtWidgets.QLabel(f'<h3>{laserName}<h3>')
        nameLabel.setAlignment(QtCore.Qt.AlignVCenter)
        color = guitools.colorutils.wavelengthToHex(wavelength)
        nameLabel.setStyleSheet(f'font-size: 16px; padding-left: 8px; border-left: 4px solid {color}')

        self.grid.addWidget(nameLabel, len(self.laserModules), 0)
        self.grid.addWidget(control, len(self.laserModules), 1)
        self.laserModules[laserName] = control

    def isLaserActive(self, laserName):
        """ Returns whether the specified laser is powered on. """
        return self.laserModules[laserName].isActive()

    def getValue(self, laserName):
        """ Returns the value of the specified laser, in the units that the
        laser uses. """
        return self.laserModules[laserName].getValue()

    def setLaserActive(self, laserName, active):
        """ Sets whether the specified laser is powered on. """
        self.laserModules[laserName].setActive(active)

    def setLaserActivatable(self, laserName, activatable):
        self.laserModules[laserName].setActivatable(activatable)

    def setLaserEditable(self, laserName, editable):
        self.laserModules[laserName].setEditable(editable)

    def setValue(self, laserName, value):
        """ Sets the value of the specified laser, in the units that the laser
        uses. """
        self.laserModules[laserName].setValue(value)

    def eventFilter(self, source, event):
        if source is self.gridContainer and event.type() == QtCore.QEvent.Resize:
            width = self.gridContainer.minimumSizeHint().width()\
                     + self.scrollArea.verticalScrollBar().width()
            self.scrollArea.setMinimumWidth(width)
            self.setMinimumWidth(width)

        return False


class LaserModule(QtWidgets.QFrame):
    """ Module from LaserWidget to handle a single laser. """

    sigEnableChanged = QtCore.Signal(bool)  # (enabled)
    sigValueChanged = QtCore.Signal(float)  # (value)

    def __init__(self, name, units, wavelength, valueRange, tickInterval, singleStep,
                 initialPower, *args, **kwargs):
        super().__init__(*args, **kwargs)
        isBinary = valueRange is None

        # Graphical elements
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)

        self.setPointLabel = QtWidgets.QLabel('Setpoint')
        self.setPointLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.setPointEdit = QtWidgets.QLineEdit(str(initialPower))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)

        self.powerLabel = QtWidgets.QLabel('Power')
        self.powerLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.powerIndicator = QtWidgets.QLabel(str(initialPower))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)

        self.minpower = QtWidgets.QLabel()
        self.minpower.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.maxpower = QtWidgets.QLabel()
        self.maxpower.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)

        if not isBinary:
            valueRangeMin, valueRangeMax = valueRange

            self.minpower.setText(str(valueRangeMin))
            self.maxpower.setText(str(valueRangeMax))

            self.slider.setMinimum(valueRangeMin)
            self.slider.setMaximum(valueRangeMax)
            self.slider.setTickInterval(tickInterval)
            self.slider.setSingleStep(singleStep)
            self.slider.setValue(0)

        powerFrame = QtWidgets.QFrame(self)
        self.powerGrid = QtWidgets.QGridLayout()
        powerFrame.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
        powerFrame.setLayout(self.powerGrid)

        self.powerGrid.addWidget(self.setPointLabel, 0, 0, 1, 2)
        self.powerGrid.addWidget(self.setPointEdit, 1, 0)
        self.powerGrid.addWidget(QtWidgets.QLabel(units), 1, 1)
        self.powerGrid.addWidget(self.powerLabel, 0, 2, 1, 2)
        self.powerGrid.addWidget(self.powerIndicator, 1, 2)
        self.powerGrid.addWidget(QtWidgets.QLabel(units), 1, 3)
        self.powerGrid.addWidget(self.minpower, 0, 4, 2, 1)
        self.powerGrid.addWidget(self.slider, 0, 5, 2, 5)
        self.powerGrid.addWidget(self.maxpower, 0, 10, 2, 1)

        self.enableButton = guitools.BetterPushButton('ON')
        self.enableButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.enableButton.setCheckable(True)

        # Add elements to QHBoxLayout
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.layout.addWidget(powerFrame)
        if isBinary:
            sizePolicy = powerFrame.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)
            powerFrame.setSizePolicy(sizePolicy)
            powerFrame.hide()
        self.layout.addWidget(self.enableButton)

        # Connect signals
        self.enableButton.toggled.connect(self.sigEnableChanged)
        self.slider.valueChanged[int].connect(
            lambda value: self.sigValueChanged.emit(float(value))
        )
        self.setPointEdit.returnPressed.connect(
            lambda: self.sigValueChanged.emit(self.getValue())
        )

    def isActive(self):
        """ Returns whether the laser is powered on. """
        return self.enableButton.isChecked()

    def getValue(self):
        """ Returns the value of the laser, in the units that the laser
        uses. """
        return float(self.setPointEdit.text())

    def setActive(self, active):
        """ Sets whether the laser is powered on. """
        self.enableButton.setChecked(active)

    def setActivatable(self, activatable):
        self.enableButton.setEnabled(activatable)

    def setEditable(self, editable):
        self.setPointEdit.setEnabled(editable)
        self.slider.setEnabled(editable)

    def setValue(self, value):
        """ Sets the value of the laser, in the units that the laser uses. """
        self.setPointEdit.setText(str(value))
        self.slider.setValue(value)


# Copyright (C) 2017 Federico Barabas 2020, 2021 TestaLab
# This file is part of Tormenta and ImSwitch.
#
# Tormenta and ImSwitch are free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tormenta and Imswitch are distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


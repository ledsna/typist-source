import os
import sys
import json
import random
import pyqtgraph as qtg
from datetime import datetime
from fractions import Fraction
from greeting import Ui_MainWindow as GreetingUI
from PyQt5.QtCore import Qt, QRect, QTimer, QEvent
from new_lesson import Ui_MainWindow as AddLessonUI
from choose_lesson import Ui_MainWindow as LessonUI
from main_interface import Ui_MainWindow as SessionUI
from PyQt5.QtGui import QFont, QTextOption, QTextCursor
from past_sessions import Ui_MainWindow as PastSessionsUI
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QTextEdit, QSizePolicy, QWidget, QLineEdit, QPushButton,
                             QListWidgetItem)


class UsernameField(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrame(False)
        # self.setMaxLength(20)

    def keyPressEvent(self, event):
        if event.key() != Qt.Key_Space:
            super().keyPressEvent(event)


class PastSessions(QMainWindow, PastSessionsUI):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setupUi(self)
        self.setWindowTitle("")
        self.speedHistory = []
        self.sessionList.setEnabled(True)
        self.detailsButton.clicked.connect(self.choose_past_session)
        self.sessionBase = []
        self.update_list()

    def closeEvent(self, event):
        self.parent.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def update_list(self):
        self.sessionList.clear()
        self.sessionBase.clear()
        self.speedHistory.clear()
        for session in self.parent.session_history["All Sessions"][::-1]:
            self.speedHistory.append(session["avg"])
            item = QListWidgetItem(f"{session['name']} | {session['date']}")
            item.setTextAlignment(int(Qt.AlignVCenter) | int(Qt.AlignHCenter))
            self.sessionList.addItem(item)
            self.sessionBase.append(session)
        self.speedHistory = self.speedHistory[::-1]
        self.plot_results()

    def plot_results(self):
        self.graphWidget.clear()
        self.graphWidget.hide()
        if self.parent.darkMode:
            self.graphWidget.setBackground((9, 17, 25, 255))
        else:
            self.graphWidget.setBackground((0, 120, 225, 255))

        base_color = (159, 208, 255, 255) if not self.parent.darkMode else (48, 62, 77, 255)
        self.graphWidget.plot([x for x in range(len(self.speedHistory))],
                              [y for y in self.speedHistory],
                              pen=qtg.mkPen(base_color, width=5))
        self.graphWidget.show()

    def choose_past_session(self):
        try:
            chosen_session = self.sessionList.selectedItems()[0].text()
            mistakes = "Mistakes: " if self.parent.language == "US" else "Ошибок: "
            speed = " cpm" if self.parent.language == "US" else " с/м"
            for session in self.parent.session_history["All Sessions"]:
                if chosen_session.split(' | ')[-1] == session["date"]:
                    self.finalTime.setText(f"{session['time']}")
                    self.finalMistakes.setText(f"{mistakes}{str(session['mistakes'])}")
                    self.finalSpeed.setText(f"{str(session['avg'])}{speed}")
            self.graphWidget.hide()
        except:
            pass


class AddLesson(QMainWindow, AddLessonUI):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setupUi(self)
        self.lessonName.setFrame(False)
        self.lessonName.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.createButton.clicked.connect(self.add_lesson)
        # self.lessonName.setMaxLength(30)
        self.setWindowTitle("")

    def add_lesson(self):
        tags = []
        if self.tagUS.isChecked():
            tags.append("US")
        if self.tagRU.isChecked():
            tags.append("RU")

        lesson_index = self.parent.parent.settings.get("user_lesson_index", 0)
        lesson_filename = "user_lesson" + str(lesson_index)
        self.parent.parent.settings["user_lesson_index"] = lesson_index + 1
        if not lesson_filename.endswith(".txt"):
            lesson_filename = lesson_filename + ".txt"
        lesson_filename = lesson_filename.replace("/", "")
        if lesson_filename and self.lessonName.text() and self.newLessonText.toPlainText():
            self.parent.parent.lessons["All Lessons"].append({lesson_filename: {"name": self.lessonName.text(),
                                                                                "tags": tags}})
            with open(resource_path("lessons.json"), "w") as lessons_json:
                json.dump(self.parent.parent.lessons, lessons_json)

            with open(resource_path(f"lessons/{lesson_filename}"), "w") as lesson_file:
                lesson_file.write(self.newLessonText.toPlainText())

            self.parent.update_list()
            self.lessonName.setText("")
            self.newLessonText.setPlainText("")
            self.tagRU.setChecked(False)
            self.tagUS.setChecked(False)
            self.lessonName.clearFocus()
            self.newLessonText.clearFocus()
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


class Greeting(QMainWindow, GreetingUI):
    def __init__(self):
        global session
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("")
        self.usernameField.hide()
        self.language_and_layout = None
        self.session = session
        if session.darkMode:
            self.setStyleSheet(session.styleSheet())
            set_ss_for(self.buttonRU, color=get_color(session.pause))
            set_ss_for(self.buttonRU, bd_color=get_color(session.pause))
            set_ss_for(self.buttonUS, color=get_color(session.pause))
            set_ss_for(self.buttonUS, bd_color = get_color(session.pause))
            set_ss_for(self.usernameField, color=get_color(session.pause))
            set_ss_for(self.usernameField, bd_color=get_color(session.pause))

        self.buttonRU.clicked.connect(self.switch_layout_and_language_to_ru)
        self.buttonUS.clicked.connect(self.switch_layout_and_language_to_us)
        username_field_font = self.usernameField.font()
        username_field_style_sheet = self.usernameField.styleSheet()
        username_field_font.setItalic(False)
        self.usernameField = UsernameField(self)
        self.usernameField.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.usernameField.setGeometry(QRect(40, 220, 450, 70))
        self.usernameField.setFont(username_field_font)
        self.usernameField.setStyleSheet(username_field_style_sheet)
        self.usernameField.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        self.usernameField.returnPressed.connect(self.finish_greeting)
        self.usernameField.setText("")
        self.usernameField.hide()

    def reset(self):
        set_ss_for(self, bg_color=get_bg_color(self.session))
        p_c = get_color(self.session.pause)
        set_ss_for(self.buttonRU, bd_color=p_c)
        set_ss_for(self.buttonRU, color=p_c)
        set_ss_for(self.buttonUS, bd_color=p_c)
        set_ss_for(self.buttonUS, color=p_c)
        set_ss_for(self.usernameField, bd_color=p_c)
        set_ss_for(self.usernameField, color=p_c)
        self.usernameField.setText("")
        self.usernameField.hide()
        self.buttonRU.show()
        self.buttonUS.show()

    def switch_layout_and_language_to_ru(self):
        self.language_and_layout = "RU"
        self.usernameField.setPlaceholderText("Имя пользователя")
        self.proceed_to_getting_username()

    def switch_layout_and_language_to_us(self):
        self.language_and_layout = "US"
        self.usernameField.setPlaceholderText("Username")
        self.proceed_to_getting_username()

    def proceed_to_getting_username(self):
        self.buttonRU.hide()
        self.buttonUS.hide()
        self.usernameField.show()

    def finish_greeting(self):
        username = self.usernameField.text()
        if not 5 <= len(username):
            return
        self.session.settings["username"] = username
        self.session.username.setText(("Привет, " if self.language_and_layout == "RU" else "Hi, ") +
                                      session.settings["username"] + "!")
        self.session.language = self.language_and_layout
        self.session.translate_session()
        self.session.show()
        self.session.settings["launched"] = 1
        self.session.settings["language"] = self.language_and_layout
        self.close()


class Lesson(QMainWindow, LessonUI):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("")
        self.parent = parent
        self.tags = []
        self.tagUS.toggled.connect(self.filter_by_tags)
        self.tagRU.toggled.connect(self.filter_by_tags)
        if parent.language == "RU":
            self.chooseButton.setText("Выбрать")
        self.chooseButton.clicked.connect(self.choose_lesson)
        self.update_list()
        self.addLesson = AddLesson(self)
        self.addButton.clicked.connect(self.add_lesson)

    def add_lesson(self):
        self.addLesson.show()

    def update_list(self):
        self.lessonList.clear()
        for lesson in self.parent.lessons["All Lessons"]:
            lesson_name = list(lesson.values())[0]["name"]
            lesson_item = QListWidgetItem(lesson_name)
            lesson_item.setTextAlignment(int(Qt.AlignVCenter) | int(Qt.AlignHCenter))
            self.lessonList.addItem(lesson_item)

    def choose_lesson(self):
        if self.lessonList.selectedItems():
            chosen_lesson = self.lessonList.selectedItems()[0].text()
            for i in self.parent.lessons["All Lessons"]:
                if list(i.values())[0]["name"] == chosen_lesson:
                    self.parent.settings["current_lesson"] = list(i.keys())[0]
            self.parent.start_session()
            self.close()

    def filter_by_tags(self):
        if self.tagUS.isChecked():
            self.tags.append("US")
        if self.tagRU.isChecked():
            self.tags.append("RU")

        self.update_list()

        items = [self.lessonList.item(i) for i in range(self.lessonList.count())]

        for item in items:
            for tag in self.tags:
                for lesson in self.parent.lessons["All Lessons"]:
                    if list(lesson.values())[0]["name"] == item.text() and tag not in list(lesson.values())[0]["tags"]:
                        self.lessonList.takeItem(self.lessonList.row(item))
                        continue

        self.tags = []

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Backspace:

            for lesson in self.parent.lessons["All Lessons"]:
                if self.lessonList.selectedItems():
                    if list(lesson.values())[0]["name"] == self.lessonList.selectedItems()[0].text():
                        if "default" not in list(lesson.values())[0]["tags"]:
                            del self.parent.lessons["All Lessons"][self.parent.lessons["All Lessons"].index(lesson)]
                            self.update_list()

                            with open(resource_path("lessons.json"), "w") as lessons_json:
                                json.dump(self.parent.lessons, lessons_json)

                            os.remove(f"lessons/{list(lesson.keys())[0]}")
                            self.parent.load_lesson()
                            self.parent.start_session()


class Session(QMainWindow, SessionUI):
    def __init__(self):
        super().__init__()
        self.aspectRatio = fr(self.width() / self.height())
        self.widthRatio = self.heightRatio = self.sizeRatio = 1
        self.lessonText = None
        self.lessons = None
        self.get_lessons()

        try:
            self.settings = json.load(open(resource_path("settings.json"), "r"))
        except:
            self.settings = {}

        try:
            self.session_history = json.load(open(resource_path("session_history.json"), "r"))
        except:
            self.session_history = {"All Sessions": []}

        self.language = self.settings.get("language")

        qtg.setConfigOption('background', None)
        qtg.setConfigOption('foreground', (32, 32, 32, 0))

        self.setupUi(self)
        self.username.clicked.connect(self.logout)
        self.pastResultsButton.clicked.connect(self.show_past_sessions)
        self.setWindowTitle("")

        self.chooseLesson = Lesson(self)
        self.chooseLesson.lessonList.setEnabled(True)

        self.typeLine = SingleLineEdit(self)

        self.graphWidget.defaultPlotLineWidth = 10
        self.graphWidget.plotLineWidth = self.graphWidget.defaultPlotLineWidth
        self.graphWidget.getPlotItem().hideAxis('bottom')
        self.graphWidget.getPlotItem().hideAxis('left')
        self.graphWidget.setGeometry(-68, self.graphWidget.y() + 50, self.baseSize().width() + 150,
                                     self.graphWidget.height() - 30)
        self.graphWidget.defaultGeometry = (-68, self.graphWidget.y() + 50, self.baseSize().width() + 150,
                                            self.graphWidget.height() - 30)

        self.progressBar.setTextVisible(False)

        self.textField.setText = self.textField.setPlainText
        self.textField.text = self.textField.toPlainText
        self.textField.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textField.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.keyboardLayout = {"Q": self.keyQ, "W": self.keyW, "E": self.keyE, "R": self.keyR, "T": self.keyT,
                               "Y": self.keyY, "U": self.keyU, "I": self.keyI, "O": self.keyO, "P": self.keyP,
                               "[": self.keyLeftBracket, "]": self.keyRightBracket, "\\": self.keyBackslash,
                               "A": self.keyA, "S": self.keyS, "D": self.keyD, "F": self.keyF, "G": self.keyG,
                               "H": self.keyH, "J": self.keyJ, "K": self.keyK, "L": self.keyL,
                               ";": self.keySemicolon, "'": self.keyQuote, "Z": self.keyZ, "X": self.keyX,
                               "C": self.keyC, "V": self.keyV, "B": self.keyB, "N": self.keyN, "M": self.keyM,
                               ",": self.keyComma, ".": self.keyDot, "/": self.keySlash, "{": self.keyLeftBracket,
                               "|": self.keyBackslash, ":": self.keySemicolon, '"': self.keyQuote,
                               "<": self.keyComma, ">": self.keyDot, "?": self.keySlash, " ": self.keySpace}

        self.ruLayout, self.usLayout = "ЙЦУКЕНГШЩЗХЪЁФЫВАПРОЛДЖЭЯЧСМИТЬБЮ/", "QWERTYUIOP[]/\ASDFGHJKL;'ZXCVBNM,."
        self.ruShiftLayout, self.usShiftLayout = '[№,.;/', '@#$^&*{}|<>'
        self.inputLanguage = "us"

        layout_list = [(k, v) for k, v in self.keyboardLayout.items()]
        self.possibleHighlightedKeys = [i[1] for i in layout_list]
        for i in range(len(self.ruLayout)):
            self.keyboardLayout[self.ruLayout[i]] = layout_list[i][1]

        self.darkMode, self.darkToLight, self.lightToDark = not self.settings.get("dark_mode"), False, False
        self.palette, self.backgroundPalette, self.borderPalette = {}, {}, {}
        self.colorMap, self.backgroundColorMap, self.borderColorMap = None, None, None
        self.typingSpeedList, self.keysToFade = [], []
        (self.basePositions, self.centeredPositions, self.baseLineWidths, self.baseBorderWidths, self.fontSizes,
         self.baseBorderRadiuses) = ({}, {}, {}, {}, {}, {})
        self.set_base_coordinates()

        self.mistakesAmount = 0
        self.timeTyping, self.inactiveFor = 0, 0  # in tenths of seconds
        self.isPaused, self.sessionStarted, self.sessionFinished = False, False, False

        self.darkToLightTime, self.lightToDarkTime = 0, 0
        self.sessionTimer, self.inactiveTimer, self.keyFadeTimer = QTimer(self), QTimer(self), QTimer(self)

        self.sessionTimer.timeout.connect(self.update_stopwatch)
        self.inactiveTimer.timeout.connect(self.idle)
        self.keyFadeTimer.timeout.connect(self.fade_keys)
        self.set_resolution()
        self.graphWidget.hide()
        if self.settings.get("username"):
            self.username.setText(("Привет, " if self.language == "RU" else "Hi, ") +
                                  self.settings.get("username") + "!")
        self.pastSessions = PastSessions(self)
        self.start_session()
        self.switch_dark_mode()
        self.change_depending_style_sheets()
        self.translate_session()
        self.update_mistakes_counter()

    def show_past_sessions(self):
        self.hide()
        self.pastSessions.update_list()
        self.pastSessions.show()
        self.pastSessions.graphWidget.show()

    def logout(self):
        global greeting
        self.hide()
        greeting.reset()
        greeting.show()

    def get_lessons(self):
        try:
            self.lessons = json.load(open(resource_path("lessons.json"), "r"))
        except Exception as e:
            self.lessons = {"All Lessons": []}
            print(e)

    def set_resolution(self):
        resolution_to_be_set = self.settings.get("resolution")
        if resolution_to_be_set:
            self.resize(*resolution_to_be_set)

    def closeEvent(self, event):
        self.settings["resolution"] = (self.size().width(), self.size().height())
        self.settings["dark_mode"] = self.darkMode
        with open(resource_path("settings.json"), "w") as settings_json:
            json.dump(self.settings, settings_json)
        return super().closeEvent(event)

    def plot_typing_speed(self):
        self.graphWidget.clear()
        self.graphWidget.hide()
        if self.darkMode:
            self.graphWidget.setBackground((9, 17, 25, 255))
        else:
            self.graphWidget.setBackground((0, 120, 225, 255))

        base_color = (159, 208, 255, 255) if not self.darkMode else (48, 62, 77, 255)
        self.graphWidget.plot([-1, -0.999999999999] + [x for x in range(len(self.typingSpeedList[1:]))],
                              [y for y in ([0, 0] + self.typingSpeedList[1:])],
                              pen=qtg.mkPen(base_color, width=self.graphWidget.plotLineWidth))
        self.graphWidget.show()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if event.oldState() and Qt.WindowMinimized:
                self.pause_session()
            elif event.oldState() == Qt.WindowNoState:
                pass
            elif self.windowState() == Qt.WindowMaximized:
                if self.sessionStarted and not self.sessionFinished:
                    pass

    def keyPressEvent(self, event):
        self.typeLine.keyPressEvent(event)

    def keyPressed(self):
        self.key_reset()
        self.keyFadeTimer.start(5)

        self.insert.show()
        modifier = QApplication.keyboardModifiers()
        highlight = True

        key_object = self.keyboardLayout.get(self.typeLine.text()[-1].upper())
        key = self.typeLine.text()[-1]

        if modifier == Qt.ShiftModifier:
            if key.upper() != key.lower():
                if key in self.ruLayout:
                    self.inputLanguage = "ru"
                elif key in self.usLayout:
                    self.inputLanguage = "us"
            else:
                if key in self.usShiftLayout:
                    highlight = False
                    self.inputLanguage = "us"
                elif key in self.ruShiftLayout:
                    highlight = False
                    self.inputLanguage = "ru"

        else:
            if key.upper() in self.ruLayout and key.upper() not in self.usLayout:
                self.inputLanguage = "ru"
            elif key.upper() not in self.ruLayout and key.upper() in self.usLayout:
                self.inputLanguage = "us"

        true_letter = self.textField.text()[0]
        if key == true_letter:
            self.askForLayoutSwitch.hide()
            self.textField.setText(self.textField.text()[1:])
            if not self.sessionStarted:
                self.sessionStarted = True
                self.sessionTimer.start(100)
            self.progressBar.setValue(int(round(len(self.typeLine.text()) /
                                                len(self.lessonText), 2) * 100))
            if key_object:
                self.key_correct(key, key_object, highlight=highlight)

            if self.textField.text() == "":
                self.sessionFinished = True
                self.insert.hide()
                self.finish_session()
                self.key_reset()
                return

        else:
            self.typeLine.setText(self.typeLine.text()[:-1])
            clause1 = (true_letter.upper() in self.ruLayout and self.inputLanguage != "ru")
            clause2 = (true_letter.upper() in self.usLayout and self.inputLanguage != "us")
            if true_letter.upper() != true_letter.lower() and (clause1 or clause2):
                self.askForLayoutSwitch.show()
                for kw, button in self.keyboardLayout.items():
                    if button != self.keySpace:
                        self.key_incorrect(kw, button, enlarge=False, colors=[2, 1, 0])
            else:
                self.askForLayoutSwitch.hide()
                if key_object:
                    self.key_incorrect(key, key_object, highlight=highlight)

            self.update_mistakes_counter()

        self.update_kb_layout()

    def translate_session(self):
        if self.language == "RU":
            self.typingSpeed.setText("0с/м")
            self.pause.setText("ПАУЗА")
            self.finished.setText("ЗАВЕРШЕНО")
            self.askForLayoutSwitch.setText("Поменяйте раскладку!")
            self.chooseLesson.chooseButton.setText("Выбрать")
            self.chooseLesson.addButton.setText("Добавить")
            self.chooseLesson.addLesson.lessonName.setPlaceholderText("Название урока")
            self.chooseLesson.addLesson.newLessonText.setPlaceholderText("Текст урока")
            self.chooseLesson.addLesson.createButton.setText("Создать")
            self.pastSessions.detailsButton.setText("Подробности")
            self.pastResultsButton.setText("Прошлые результаты")

        elif self.language == "US":
            self.typingSpeed.setText("0cpm")
            self.pause.setText("PAUSED")
            self.finished.setText("FINISHED")
            self.askForLayoutSwitch.setText("Switch layout!")
            self.chooseLesson.chooseButton.setText("Choose")
            self.chooseLesson.addButton.setText("Add")
            self.chooseLesson.addLesson.lessonName.setPlaceholderText("Lesson Name")
            self.chooseLesson.addLesson.newLessonText.setPlaceholderText("Lesson Text")
            self.chooseLesson.addLesson.createButton.setText("Create")
            self.pastSessions.detailsButton.setText("Details")
            self.pastResultsButton.setText("Past Results")

        self.stopwatch.setText("0.0")
        self.update_mistakes_counter()

    def start_session(self):
        self.translate_session()
        self.inactiveTimer.start(100)
        self.keyFadeTimer.start(5)
        self.sessionTimer.stop()
        self.insert.show()
        self.isPaused = False
        self.set_layouts()
        self.update_kb_layout()
        self.key_reset()
        self.timeTyping, self.inactiveFor = 0, 0
        self.typingSpeedList.clear()
        self.sessionFinished = False
        self.sessionStarted = False
        if self.isPaused:
            self.unpause_session()
        self.typeLine.previousText = ""
        self.typeLine.setText('')
        self.mistakesAmount = 0
        self.progressBar.setValue(0)

        self.finished.hide()
        self.pause.hide()
        self.stopwatch.show()
        self.askForLayoutSwitch.hide()
        self.update_mistakes_counter()

        self.update_palette()
        self.set_palette()
        self.load_lesson()

    def finish_session(self):
        for lesson in self.lessons["All Lessons"]:
            if list(lesson.keys())[0] == self.settings["current_lesson"]:
                lesson_name = list(lesson.values())[0]["name"]
                break

        self.session_history["All Sessions"].append({"name": lesson_name,
                                                     "date": '.'.join(str(datetime.now()).split('.')[:-1]),
                                                     "max": int(max(self.typingSpeedList)),
                                                     "avg": int(sum(self.typingSpeedList) / len(self.typingSpeedList)),
                                                     "mistakes": self.mistakesAmount,
                                                     "time": self.stopwatch.text()})

        with open(resource_path("session_history.json"), "w") as session_history_file:
            json.dump(self.session_history, session_history_file)
        self.stopwatch.hide()
        self.finished.show()
        self.pastSessions.update_list()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.widthRatio = fr(self.width() / self.baseSize().width())
        self.heightRatio = fr(self.height() / self.baseSize().height())

        self.sizeRatio = min(self.widthRatio, self.heightRatio)

        for window_object in self.findChildren(QWidget):
            if self.fontSizes.get(window_object):
                font = window_object.font()
                font.setPointSize(int(self.sizeRatio * self.fontSizes[window_object]))
                window_object.setFont(font)
            if window_object in (self.progressBar, self.graphWidget, self.typeLine, self.textField):
                self.center_object(window_object, stretched=True)
            elif type(window_object) == QLabel or type(window_object) == QPushButton:
                self.center_object(window_object)

            if "border-width" in window_object.styleSheet():
                bw = str(round(self.sizeRatio * self.baseBorderWidths[window_object], 2))
                set_ss_for(window_object, b_width=bw)

            if "border-radius" in window_object.styleSheet():
                br = str(round(self.sizeRatio * self.baseBorderRadiuses[window_object], 2))
                set_ss_for(window_object, b_radius=br)

            if type(window_object) == QLabel:
                window_object.setLineWidth(max(round(self.sizeRatio * self.baseLineWidths[window_object]), 1))

        self.typeLine.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.graphWidget.plotLineWidth = int(self.sizeRatio * self.graphWidget.defaultPlotLineWidth)
        font = self.typeLine.font()
        font.setPointSize(int(fr(self.sizeRatio * self.fontSizes[self.typeLine])))
        self.typeLine.setFont(font)

        font.setBold(True)
        font.setItalic(False)
        self.textField.setFont(font)
        usr_geometry = self.username.geometry()
        self.username.setGeometry(usr_geometry.x(), self.keySpace.geometry().bottom() +
                                  (self.height() -self.keySpace.geometry().bottom()) // 2 - usr_geometry.height() // 2,
                                  usr_geometry.width(), usr_geometry.height())

    def center_object(self, window_object, stretched=False):
        if stretched:
            x = fr(self.widthRatio * self.basePositions[window_object][0])
            w = fr(self.widthRatio * window_object.baseSize().width())
        else:
            x = fr(self.sizeRatio * self.centeredPositions[window_object][0] + self.width() / 2)
            w = fr(self.sizeRatio * window_object.baseSize().width())
        y = fr(self.sizeRatio * self.centeredPositions[window_object][1] + self.height() / 2)
        h = fr(self.sizeRatio * window_object.baseSize().height())
        window_object.setGeometry(QRect(*map(int, [x, y, w, h])))

    def pause_session(self):
        self.chooseLesson.show()
        if self.sessionStarted and not self.sessionFinished:
            self.isPaused = True
            self.sessionTimer.stop()
            self.keyFadeTimer.stop()
            self.pause.show()
            self.stopwatch.hide()

    def unpause_session(self):
        if self.sessionStarted and not self.sessionFinished:
            self.isPaused = False
            self.sessionTimer.start(100)
            self.keyFadeTimer.start(5)
            self.pause.hide()
            self.stopwatch.show()

    def switch_dark_mode(self):
        self.darkToLight = self.darkMode
        self.darkMode = not self.darkMode
        self.lightToDark = not self.darkMode
        self.lightToDarkTime *= int(self.lightToDark)
        self.darkToLightTime *= int(self.darkToLight)
        self.update_palette()
        self.set_palette()
        self.plot_typing_speed()
        self.change_depending_style_sheets()

    def change_depending_style_sheets(self):
        global greeting
        self.chooseLesson.setStyleSheet(self.styleSheet())
        self.chooseLesson.addLesson.setStyleSheet(self.styleSheet())
        if self.darkMode:
            set_ss_for(self.chooseLesson.lessonList, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.chooseButton, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.addButton, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.chooseButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addLesson.lessonName, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.tagUS, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.tagRU, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.addLesson.tagUS, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.addLesson.tagRU, color=get_color(self.textField))
            set_ss_for(self.chooseLesson.addLesson.createButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addLesson.createButton, color=get_color(self.pause))
            set_ss_for(self.pastSessions.sessionList, color=get_color(self.textField))
            set_ss_for(self.pastSessions, bg_color=get_bg_color(self))
            set_ss_for(self.pastSessions.detailsButton, color=get_color(self.pause))
            set_ss_for(self.pastSessions.detailsButton, bd_color=get_color(self.pause))
            set_ss_for(self.pastResultsButton, color=get_color(self.pause))
            set_ss_for(self.pastResultsButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addLesson.newLessonText, color=get_color(self.pause))
            for item in (self.pastSessions.finalSpeed, self.pastSessions.finalTime, self.pastSessions.finalMistakes):
                set_ss_for(item, color=get_color(self.pause))
                set_ss_for(item, bd_color=get_color(self.pause))

        else:
            set_ss_for(self.pastSessions, bg_color=get_bg_color(self))
            set_ss_for(self.pastSessions.detailsButton, color=get_color(self.pause))
            set_ss_for(self.pastSessions.detailsButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.lessonList, color=get_color(self.typeLine))
            set_ss_for(self.pastSessions.sessionList, color=get_color(self.typeLine))
            set_ss_for(self.chooseLesson.chooseButton, color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addButton, color=get_color(self.pause))
            set_ss_for(self.chooseLesson.chooseButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addLesson.lessonName, color=get_color(self.pause))
            set_ss_for(self.chooseLesson.tagUS, color=get_color(self.typeLine))
            set_ss_for(self.chooseLesson.tagRU, color=get_color(self.typeLine))
            set_ss_for(self.chooseLesson.addLesson.tagUS, color=get_color(self.typeLine))
            set_ss_for(self.chooseLesson.addLesson.tagRU, color=get_color(self.typeLine))
            set_ss_for(self.chooseLesson.addLesson.createButton, bd_color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addLesson.createButton, color=get_color(self.pause))
            set_ss_for(self.pastResultsButton, color=get_color(self.pause))
            set_ss_for(self.chooseLesson.addLesson.newLessonText, color=get_color(self.pause))
            set_ss_for(self.pastResultsButton, bd_color=get_color(self.pause))
            for item in (self.pastSessions.finalSpeed, self.pastSessions.finalTime, self.pastSessions.finalMistakes):
                set_ss_for(item, color=get_color(self.pause))
                set_ss_for(item, bd_color=get_color(self.pause))

    def idle(self):
        if self.sessionStarted and not self.isPaused and not self.sessionFinished:
            self.inactiveFor += 1
            if self.inactiveFor / 10 > 20:
                self.pause_session()
            if self.inactiveFor % 4 == 0:
                if self.insert.isHidden():
                    self.insert.show()
                else:
                    self.insert.hide()

    def update_stopwatch(self):
        if not self.isPaused and not self.sessionFinished:
            delta = 20
            if self.darkToLight:
                self.darkToLightTime += 1
                if self.darkToLightTime >= delta:
                    self.darkToLight = False
            if self.lightToDark:
                self.lightToDarkTime += 1
                if self.lightToDarkTime >= delta:
                    self.lightToDark = False

            self.timeTyping += 1
            self.plot_typing_speed()
            minutes = self.timeTyping // 600
            seconds = fr(self.timeTyping % 600 / 10)
            if minutes:
                seconds = str(seconds).split('.')[0].zfill(2)
            self.stopwatch.setText(f"{str(minutes) + ':' if minutes else ''}{seconds}")
            typing_speed = int(len(self.typeLine.text()) / (self.timeTyping / 10) * 60)
            self.typingSpeedList.append(typing_speed)
            self.typingSpeed.setText(str(typing_speed) + ("cpm" if self.language == "US" else "с/м"))

    def update_mistakes_counter(self):
        self.mistakesMade.setText(("Mistakes: " if self.language == "US" else "Ошибок: ") + str(self.mistakesAmount))

    def update_kb_layout(self):
        if self.inputLanguage == "ru":
            for text, key_obj in self.keyboardLayout.items():
                if text in self.ruLayout:
                    key_obj.setText(text)
        else:
            for text, key_obj in self.keyboardLayout.items():
                if text in self.usLayout:
                    key_obj.setText(text)

    def key_reset(self):
        for key in [v for k, v in self.keyboardLayout.items()]:
            self.keysToFade.append(key)
            self.center_object(key)

    def key_correct(self, key, key_object, highlight=True):
        if highlight:
            reduced_bg_color = multiply_color(get_bg_color(key_object), 0.77 if not self.darkMode else 2.5)
            set_ss_for(key_object, bg_color=reduced_bg_color)
            if key not in [" ", ]:
                enlarge_key(key_object, 1 / 10)

    def key_incorrect(self, key, key_object, highlight=True, enlarge=True, colors=None):
        if not colors:
            colors = [0, 1, 2]
            self.mistakesAmount += 1

        if highlight:
            if not self.darkMode:
                redder_color = list(rgba_to_tuple(get_bg_color(key_object)))
                if enlarge:
                    redder_color_red = 255
                    redder_color_green = redder_color[colors[1]] // 2 + 20
                    redder_color_blue = redder_color[colors[2]] // 6
                    redder_color = str((redder_color_red, redder_color_green, redder_color_blue, 255))
                    bg_color = f"rgba{redder_color};"
                else:
                    bg_color = "rgba(255, 255, 255, 100);"
            else:
                bg_color = "rgba(70, 20, 20, 100);"
            set_ss_for(key_object, bg_color=bg_color)
            if key not in [" ", ] and enlarge:
                enlarge_key(key_object, 1 / 10)

    def fade_keys(self):
        for key_object in self.keysToFade:
            if key_object in self.backgroundPalette:
                clause = self.darkToLight or self.darkMode and not self.lightToDark
                default_bg_color = rgba_to_tuple(self.backgroundPalette[key_object])
                current_bg_color = rgba_to_tuple(get_bg_color(key_object))
                default_color = get_color(key_object)
                colors = zip(default_bg_color, current_bg_color)
                divisor = random.randint(1, 40) if clause else 7
                difference = tuple((round((x - y) / divisor) for x, y in colors))

                for value in difference:
                    if abs(value) < 1:
                        continue
                    break
                else:
                    difference = (0, 0, 0, 0)

                if difference != (0, 0, 0, 0):
                    color = f"{default_color}"
                    bg_color = f"rgba{str(tuple(x + y for x, y in zip(difference, current_bg_color)))};"

                    set_ss_for(key_object, color=color, bg_color=bg_color)
                else:
                    color = f"{default_color}"
                    bg_color = f"rgba{default_bg_color};"
                    set_ss_for(key_object, color=color, bg_color=bg_color)
                    del self.keysToFade[self.keysToFade.index(key_object)]

        if not self.keysToFade:
            self.keyFadeTimer.stop()

    def set_base_coordinates(self):
        for window_object in self.findChildren(QWidget):
            label_name = window_object.objectName()
            if "key" in label_name:
                self.keysToFade.append(window_object)
            window_object.setBaseSize(window_object.width(), window_object.height())
            self.basePositions[window_object] = [window_object.x(), window_object.y()]
            self.centeredPositions[window_object] = [int(window_object.x() - self.baseSize().width() / 2),
                                                     int(window_object.y() - self.baseSize().height() / 2)]

            self.fontSizes[window_object] = window_object.fontInfo().pointSize()
            if "border-width: " in window_object.styleSheet():
                widget_border_width = int(window_object.styleSheet().split("border-width: ")[1].split("px")[0])
                self.baseBorderWidths[window_object] = widget_border_width
            if "border-radius: " in window_object.styleSheet():
                widget_border_radius = int(window_object.styleSheet().split("border-radius: ")[1].split("px")[0])
                self.baseBorderRadiuses[window_object] = widget_border_radius
            try:
                self.baseLineWidths[window_object] = window_object.lineWidth()
            except AttributeError:
                pass

    def update_palette(self):
        for k, v in self.backgroundColorMap.items():
            for obj in k:
                self.backgroundPalette[obj] = v[self.darkMode]

        for k, v in self.colorMap.items():
            for obj in k:
                self.palette[obj] = v[self.darkMode]

        for k, v in self.borderColorMap.items():
            for obj in k:
                self.borderPalette[obj] = v[self.darkMode]

    def set_palette(self):
        set_ss_for(self, bg_color=self.backgroundPalette[self])
        for window_object in self.findChildren(QWidget):
            if "key" not in window_object.objectName():
                if window_object in self.backgroundPalette:
                    set_ss_for(window_object, bg_color=self.backgroundPalette[window_object])
            if window_object in self.palette:
                set_ss_for(window_object, color=self.palette[window_object])
            if window_object in self.borderPalette:
                set_ss_for(window_object, bd_color=self.borderPalette[window_object])

        self.key_reset()
        self.keyFadeTimer.start(5)

    def set_layouts(self):
        self.colorMap = \
            {
                (self.keySpace,): ["rgba(100, 100, 100, 190);", "rgba(50, 50, 46, 255);"],
                (self.textField, self.askForLayoutSwitch): ["rgba(255, 255, 255, 255);", "rgba(48, 62, 77, 255);"],
                (self.typeLine, self.username): ["rgba(255, 255, 255, 70);", "rgba(48, 62, 77, 125);"],
                (self.pause, self.stopwatch, self.typingSpeed, self.mistakesMade,):
                    ["rgba(255, 255, 255, 100);", "rgba(255, 255, 255, 30);"],
                (self.finished, self.pause, self.stopwatch, self.typingSpeed, self.mistakesMade, self.keyCaps,
                 self.keyTab, self.keyLeftShift, self.keyRightShift, self.keyReturn, self.keyFn,
                 self.keyLeftOption, self.keyRightOption, self.keyLeftCommand, self.keyRightCommand, self.keyLeftArrow,
                 self.keyUpArrow, self.keyDownArrow, self.keyRightArrow, self.keyControl):
                    ["rgba(159, 208, 255, 255);", "rgba(48, 62, 77, 255);"]}

        # (self.insert,): ["rgba(255, 255, 255, 255);", "rgba(255, 255, 255, 76);"],

        self.borderColorMap = {(self.finished, self.pause, self.stopwatch, self.typingSpeed, self.mistakesMade,
                                self.keyCaps, self.keyTab, self.keyLeftShift, self.keyRightShift, self.keyReturn,
                                self.keyFn, self.keyLeftOption, self.keyRightOption, self.keyLeftCommand,
                                self.keyRightCommand, self.keyLeftArrow, self.keyUpArrow, self.keyDownArrow,
                                self.keyRightArrow, self.keyControl):
                                   ["rgba(159, 208, 255, 255);", "rgba(48, 62, 77, 255);"]}

        # ["rgba(159, 208, 255, 255);", "rgba(48, 62, 77, 255);"]

        self.backgroundColorMap = \
            {self.get_key_set("qazp;/[']\\"): ["rgba(146, 223, 174, 255);", "rgba(43, 66, 52, 255);"],
             self.get_key_set("wsxol."): ["rgba(133, 225, 251, 255);", "rgba(39, 67, 75, 255);"],
             self.get_key_set("edcik,"): ["rgba(234, 163, 195, 255);", "rgba(70, 48, 58, 255);"],
             self.get_key_set("rfvtgb"): ["rgba(246, 193, 136, 255);", "rgba(73, 57, 40, 255);"],
             self.get_key_set("yhnujm"): ["rgba(253, 238, 142, 255);", "rgba(75, 71, 42, 255);"],
             (self.progressBar,): ["rgba(255, 255, 255, 170);", "rgba(48, 62, 77, 255);"],
             (self.insert,): ["rgba(255, 255, 255, 255);", "rgba(48, 62, 77, 255);"],
             (self.keySpace,): ["rgba(250, 250, 230, 255);", "rgba(73, 73, 68, 255);"],
             (self,): ["qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 120, 225, 255)," +
                       " stop:0.5 rgba(0, 120, 225, 255), stop:1 rgba(40, 145, 255, 255));",
                       ("qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(9, 17, 25, 255)," +
                        "stop:0.5 rgba(9, 17, 25, 255), stop:1 rgba(18, 34, 50, 255));")]}

    def load_lesson(self):
        try:
            self.lessonText = open(resource_path(f"lessons/{self.settings['current_lesson']}")).read().replace("\n", " ")
            self.textField.setText(self.lessonText)
            self.typeLine.setText("")
        except:
            if len(self.lessons['All Lessons']):
                self.settings["current_lesson"] = list(self.lessons["All Lessons"][0].keys())[0]
                self.load_lesson()
            else:
                self.typeLine.setText("")
                self.textField.setText("")

    def get_key_set(self, keys):
        key_set = tuple(map(lambda x: self.keyboardLayout[x.capitalize()], keys))
        return key_set


class SingleLineEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        type_line_font = QFont("Helvetica Neue", 60)
        type_line_font.setItalic(True)
        self.parent = parent
        self.setTabChangesFocus(True)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setGeometry(QRect(0, 437, 841, 85))
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0); color: rgba(255, 255, 255, 70);")
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setFont(type_line_font)
        self.setTextInteractionFlags(Qt.TextEditable)
        self.setCursorWidth(0)
        self.selectionChanged.connect(self.handle_selection_changes)
        self.previousText = ""
        self.noSelectionCursor = self.textCursor()
        self.setDisabled(True)

    def setText(self, text):
        self.setPlainText(text)
        self.moveCursor(QTextCursor.End)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def text(self):
        return self.toPlainText()

    def look_for_session_state_changes(self, button_pressed):
        if button_pressed == Qt.Key_Escape:
            if not self.parent.isPaused:
                self.parent.pause_session()
            else:
                self.parent.unpause_session()
        elif button_pressed == Qt.Key_AsciiTilde:
            self.parent.switch_dark_mode()
        return {"isPaused": self.parent.isPaused, "sessionStarted": self.parent.sessionStarted, "sessionFinished":
            self.parent.sessionFinished}

    def keyPressEvent(self, event):
        self.parent.inactiveFor = 0
        session_states = self.look_for_session_state_changes(event.key())

        if not self.parent.isPaused and not self.parent.sessionFinished:
            super().keyPressEvent(event)

        if len(self.text()) > len(self.previousText):
            self.parent.keyPressed()
        elif len(self.text()) < len(self.previousText):
            self.setText(self.previousText)
        self.previousText = self.text()
        self.noSelectionCursor = self.textCursor()

    def handle_selection_changes(self):
        self.setTextCursor(self.noSelectionCursor)


def enlarge_key(key_object, size_delta):
    coordinate_delta = fr(size_delta / 2)
    key_object.setGeometry(QRect(*map(int, [fr(key_object.x() - key_object.width() * coordinate_delta),
                                            fr(key_object.y() - key_object.height() * coordinate_delta),
                                            fr((size_delta + 1) * key_object.width()),
                                            fr((size_delta + 1) * key_object.height())])))


def rgba_to_tuple(rgba):
    rgba = tuple(map(int, rgba[5:rgba.index(")")].split(",")))
    return rgba


def get_color(key_object):
    stylesheet = key_object.styleSheet()
    return (stylesheet.split(" color:")[1].split(")")[0] + ");") if " color" in stylesheet else None


def get_bg_color(window_object):
    ss = window_object.styleSheet()
    if "background-color: " in ss:
        lf = "background-color: "
        lfindex = ss.find(lf) + len(lf)
        return ss[lfindex:].split(";")[0] + ";"
    return None


def get_bd_color(window_object):
    ss = window_object.styleSheet()
    if "border-color: " in ss:
        lf = "border-color: "
        lfindex = ss.find(lf) + len(lf)
        return ss[lfindex].split(";")[0] + ";"

    return None


def set_ss_for(window_object, color=None, bg_color=None, b_width=None, b_radius=None, bd_color=None):
    ss = window_object.styleSheet()

    if color and " color: " in ss:
        lf = " color: "
        lfindex = ss.find(lf) + len(lf)
        window_object.setStyleSheet(ss[:lfindex] + color + ";".join(ss[lfindex:].split(";")[1:]))
    if bg_color and "background-color: " in ss:
        lf = "background-color: "
        lfindex = ss.find(lf) + len(lf)
        window_object.setStyleSheet(ss[:lfindex] + bg_color + ";".join(ss[lfindex:].split(";")[1:]))
    if b_width and "border-width: " in window_object.styleSheet():
        bw = "border-width: "
        bwindex = ss.find(bw) + len(bw)
        window_object.setStyleSheet(ss[:bwindex] + str(b_width) + "px;" + ";".join(ss[bwindex:].split(";")[1:]))
    if b_radius and "border-radius: " in ss:
        br = "border-radius: "
        brindex = ss.find(br) + len(br)
        window_object.setStyleSheet(ss[:brindex] + str(b_radius) + "px;" + ";".join(ss[brindex:].split(";")[1:]))
    if bd_color and "border-color: " in ss:
        bdc = "border-color: "
        bdcindex = ss.find(bdc) + len(bdc)
        window_object.setStyleSheet(ss[:bdcindex] + str(bd_color) + ";".join(ss[bdcindex:].split(";")[1:]))


def multiply_color(rgba, multiplier):
    rgba = rgba_to_tuple(rgba)
    reduced_color = list(map(lambda x: round(multiplier * x), rgba[:3])) + [rgba[3]]

    for color_index in range(len(reduced_color)):
        if reduced_color[color_index] > 255:
            reduced_color[color_index] = 255

    return f"rgba({reduced_color[0]}, {reduced_color[1]}, {reduced_color[2]}, {reduced_color[3]});"


def find_layout(layouts, object_name):
    if object_name == "space":
        object_name = " "
    return next((k for k in layouts if object_name.lower() in layouts[k]))


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def fr(value):
    return float(Fraction(value).limit_denominator())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    session = Session()
    greeting = Greeting()

    if session.settings.get("launched"):
        session.show()
    else:
        greeting.show()
    sys.exit(app.exec_())

"""Excel reporting for computed player metrics and bounce points."""

import xlwt

from .data_structures import TrackingData


class ReportWriter:
    def __init__(self) -> None:
        self.workbook = xlwt.Workbook()
        self.style_headline = xlwt.easyxf('font: bold on, height 320, underline on; align: horiz left;')
        self.style_title = xlwt.easyxf('font: bold on, height 240, underline off; align: horiz left;')
        self.style_center = xlwt.easyxf('font: bold off, height 200, underline off;  align: horiz center;')
        self.style_right = xlwt.easyxf('font: bold off, height 200, underline off;  align: horiz right;')
        self.style_left = xlwt.easyxf('font: bold off, height 200, underline off;  align: horiz left;')

    def _sheet_net_height(self, data: TrackingData) -> None:
        sheet = self.workbook.add_sheet("HightOverNet")
        sheet.write(0, 0, "Abstand des Balls zum Netz", self.style_headline)
        sheet.write(2, 0, "Schlag Nr.", self.style_title)
        sheet.write(2, 1, "", self.style_title)
        sheet.write(2, 2, "Spieler 1", self.style_title)
        sheet.write(2, 3, "", self.style_title)
        sheet.write(2, 4, "Spieler 2", self.style_title)
        sheet.write(3, 6, "f.S. = fehlerhafter Schlag", self.style_left)
        for i in range(len(data.player1_net_height)):
            sheet.write(i + 3, 0, i + 1, self.style_center)
            sheet.write(i + 3, 1, "", self.style_center)
            if data.player1_net_height[i] == 'Detektion nicht moeglich':
                sheet.write(i + 3, 2, data.player1_net_height[i], self.style_left)
            else:
                sheet.write(i + 3, 2, data.player1_net_height[i], self.style_right)
            sheet.write(i + 3, 3, "", self.style_center)
            if data.player2_net_height[i] == 'Detektion nicht moeglich':
                sheet.write(i + 3, 4, data.player2_net_height[i], self.style_left)
            else:
                sheet.write(i + 3, 4, data.player2_net_height[i], self.style_right)
        sheet.col(0).width = 256 * 12
        sheet.col(1).width = 256 * 3
        sheet.col(2).width = 256 * 12
        sheet.col(3).width = 256 * 3
        sheet.col(4).width = 256 * 12
        sheet.row(0).height = (256 // 10) * 16
        sheet.row(2).height = (256 // 10) * 12

    def _sheet_speed(self, data: TrackingData) -> None:
        sheet = self.workbook.add_sheet("BallSpeed")
        sheet.write(0, 0, "Geschwindigkeit des Balls", self.style_headline)
        sheet.write(2, 0, "Schlag Nr.", self.style_title)
        sheet.write(2, 1, "", self.style_title)
        sheet.write(2, 2, "Spieler 1", self.style_title)
        sheet.write(2, 3, "", self.style_title)
        sheet.write(2, 4, "Spieler 2", self.style_title)
        sheet.write(3, 6, "f.S. = fehlerhafter Schlag", self.style_left)
        for i in range(len(data.player1_ball_speed)):
            sheet.write(i + 3, 0, i + 1, self.style_center)
            sheet.write(i + 3, 1, "", self.style_center)
            if data.player1_ball_speed[i] == 'Detektion nicht moeglich':
                sheet.write(i + 3, 2, data.player1_ball_speed[i], self.style_left)
            else:
                sheet.write(i + 3, 2, data.player1_ball_speed[i], self.style_right)
            sheet.write(i + 3, 3, "", self.style_center)
            if data.player2_ball_speed[i] == 'Detektion nicht moeglich':
                sheet.write(i + 3, 4, data.player2_ball_speed[i], self.style_left)
            else:
                sheet.write(i + 3, 4, data.player2_ball_speed[i], self.style_right)
        sheet.col(0).width = 256 * 12
        sheet.col(1).width = 256 * 3
        sheet.col(2).width = 256 * 12
        sheet.col(3).width = 256 * 3
        sheet.col(4).width = 256 * 12
        sheet.row(0).height = (256 // 10) * 16
        sheet.row(2).height = (256 // 10) * 12

    def _sheet_bounce(self, data: TrackingData) -> None:
        sheet = self.workbook.add_sheet("BallBouncePoint")
        sheet.write(0, 0, "Auftreffpunkt des Balls", self.style_headline)
        sheet.write(2, 0, "Schlag Nr.", self.style_title)
        sheet.write(2, 1, "", self.style_title)
        sheet.write(2, 2, "Spieler 1", self.style_title)
        sheet.write(2, 3, "", self.style_title)
        sheet.write(2, 4, "Spieler 2", self.style_title)
        sheet.write(3, 6, "f.S. = fehlerhafter Schlag", self.style_left)
        for i in range(len(data.player1_ball_bounce)):
            sheet.write(i + 3, 0, i + 1, self.style_center)
            sheet.write(i + 3, 1, "", self.style_center)
            if data.player1_ball_bounce[i] == 'Detektion nicht moeglich':
                sheet.write(i + 3, 2, data.player1_ball_bounce[i], self.style_left)
            else:
                sheet.write(i + 3, 2, data.player1_ball_bounce[i], self.style_right)
            sheet.write(i + 3, 3, "", self.style_center)
            if data.player2_ball_bounce[i] == 'Detektion nicht moeglich':
                sheet.write(i + 3, 4, data.player2_ball_bounce[i], self.style_left)
            else:
                sheet.write(i + 3, 4, data.player2_ball_bounce[i], self.style_right)
        sheet.col(0).width = 256 * 12
        sheet.col(1).width = 256 * 3
        sheet.col(2).width = 256 * 12
        sheet.col(3).width = 256 * 3
        sheet.col(4).width = 256 * 12
        sheet.row(0).height = (256 // 10) * 16
        sheet.row(2).height = (256 // 10) * 12
        # If you need the bitmap overlay, add it here if the resource exists
        # sheet.insert_bitmap('tischtennis-platte.bmp', 2, 8)

    def write(self, data: TrackingData, out_path: str = "TableTennisData.xls") -> None:
        self._sheet_net_height(data)
        self._sheet_speed(data)
        self._sheet_bounce(data)
        self.workbook.save(out_path)



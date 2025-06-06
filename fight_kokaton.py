import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))
NUM_OF_BOMBS = 5 #爆弾数


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0) #向き

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = sum_mv #向き記録
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")
        self.vx, self.vy = bird.dire
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 5
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 5
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), math.degrees(math.atan2(-self.vy,self.vx)), 0.9)


    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    スコア表示に関するクラス
    """
    def __init__(self, screen:pg.Surface, score=0):
        """
        スコアのテキスト生成
        引数：スコア
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255) #青
        self.img = self.fonto.render(f"score:{score}", 0, self.color)
        screen.blit(self.img, [100, HEIGHT-50])
    
    def update(self, score, screen: pg.Surface):
        """
        スコア更新
        引数 screen：画面Surface
        """
        self.score = score
        self.img = self.fonto.render(f"score:{score}", 0, self.color)
        screen.blit(self.img,[100, HEIGHT-50])


class explosion():
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb:"Bomb"):
        """
        爆発gifの表示
        """
        self.imgb = pg.transform.rotozoom(pg.image.load("fig/explosion.gif"), 0, 1.0)
        self.imgf = pg.transform.flip(self.imgb, True, True)  #反転
        self.rct = self.imgb.get_rect()
        self.rct.center = bomb.rct.center
        self.imgs = [self.imgb, self.imgf]
        self.life = 50

    def update(self, screen: pg.Surface):
        self.life -= 1
        if self.life%6>=3:
            screen.blit(self.imgs[0],self.rct)
        if self.life%6<3:
            screen.blit(self.imgs[1],self.rct)


def main():
    # 初期化
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    clock = pg.time.Clock()
    point = 0
    scores = Score(screen,point)
    beams = []
    exp = []
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)  
                beams.append(beam)          
        screen.blit(bg_img, [0, 0])
        
        # こうかとん衝突
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        
        # 爆弾破壊
       
        for j in range(len(beams)):
            if beams[j] == None:
                continue
            for i in range(len(bombs)):
                if bombs[i] != None and beams[j] != None:
                    if beams[j].rct.colliderect(bombs[i].rct):
                            # beamとbomb衝突時
                        exp.append(explosion(bombs[i])) #爆発表示
                        beams[j] = None
                        bombs[i] = None
                        point += 1 #スコア追加
                        bird.change_img(6, screen) #喜び
                        break
        bombs = [bomb for bomb in bombs if bomb is not None]
        beams = [beam for beam in beams if beam is not None]


        # アプデ
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        # ビーム
        for beam in beams:
            beam.update(screen)
            if check_bound(beam.rct) != (True, True):
                beams.remove(beam)
        # 爆弾
        for bomb in bombs:
            bomb.update(screen)
        # 爆発
        for ex in exp:
            if ex.life<0:
                exp.remove(ex)
            ex.update(screen)
        scores.update(point, screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()

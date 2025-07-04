import os
import random
import sys
import time
import math
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 画面に出現させる爆弾の数

os.chdir(os.path.dirname(os.path.abspath(__file__)))


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
        self.dire = (+5, 0)#こうかとんの向きを表すタプル,self.dire=(+5,0)を定義(デフォルト右向き)

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
            self.dire = tuple(sum_mv)#合計移動量sum_mvが[0,0]でないとき、self.direをsum_mvの値で更新する。
            self.img = __class__.imgs[tuple(sum_mv)]
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

        self.vx,self.vy=bird.dire#Birdのdireにアクセスし，こうかとんが向いている方向をvx, vyに代入
        theta = math.atan2(-self.vy, self.vx)#math.atan2(-vy, vx)で，直交座標(x, -y)から極座標の角度Θに変換
        deg = math.degrees(theta)  ## • math.degrees(Θ)で弧度法から度数法に変換し，rotozoomで回転
        img0 = pg.image.load("fig/beam.png")
        self.img = pg.transform.rotozoom(img0, deg, 1.0)  # rotozoomで回転
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx // 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy // 5#こうかとんのrctのwidthとheightおよび向いている方向を考慮した初期配置
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
    打ち落とした爆弾の数を表示するスコアクラス
    """
    def __init__(self):#イニシャライザ
        """
        スコアの初期化
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)  # フォントの設定
        self.color = (0, 0, 255)  # 色の設定。
        self.score = 0  # 初期値
        self.img = self.fonto.render(f"SCORE: {self.score}", True, self.color)
        self.rct = self.img.get_rect()#座標
        self.rct.center = (100, HEIGHT - 50)  # 左下、横100,縦は画面下部から50

    def update(self, screen: pg.Surface):#updateメソッド
        """
        スコア表示用Surfaceを更新して表示する
        """
        self.img = self.fonto.render(f"SCORE: {self.score}", True, self.color)#現在のスコア表示
        screen.blit(self.img, self.rct)

    def add_point(self):
        """
        スコアに1点加算
        """
        self.score += 1
class Explosion:
    """
    爆発を表示するクラス。
    """
                # 元のexplosion.gifと上下左右にflipしたものの2つのSurfaceをリストに格納
            #     爆発した爆弾のrct.centerに座標を設定
            #     表示時間（爆発時間）lifeを設定
    def __init__(self, center: tuple[int, int]):
        img0 = pg.image.load("fig/explosion.gif")#画像surface
        img1 = pg.transform.flip(img0, True, True)#上下左右にflipさせたもの。
        self.imgs = [img0, img1]  # 2つのsurfaceをリストに格納
        self.img = self.imgs[0]
        self.rct = self.img.get_rect()#爆発した爆弾の座標取得
        self.rct.center = center#rct.centerに設定。
        self.life=10#表示時間(爆発時間)の設定。

    def update(self, screen: pg.Surface):#updateメソッド
        self.life -= 1 #爆発経過時間lifeを１減算
        self.img = self.imgs[self.life % 2]#交互に切り替える。
        screen.blit(self.img, self.rct)
        

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bomb = Bomb((255, 0, 0), 10)
    bombs=[]#爆弾用の空リスト
    beams=[]#ビーム用の空リスト
    explosions=[]#爆発用の空リスト
    for _ in range(NUM_OF_BOMBS):#NUM_OF_BOMBSを5を代入して定義しておく。
        bombs.append(Bomb((255,0,0),10))
    #beam = None  # ゲーム初期化時にはビームは存在しない
    clock = pg.time.Clock()
    tmr = 0
    score = Score()
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))#beamsリストにappend
        screen.blit(bg_img, [0, 0])
        
        if bomb in bombs:#bombsにはnoneがない
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto=pg.font.Font(None,80)
                txt=fonto.render("Game Over",True,(255,0,0))
                screen.blit(txt,[WIDTH//2-150,HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        for i, bomb in enumerate(bombs):
            for j, beam in enumerate(beams):
                    if beam is not None and beam.rct.colliderect(bomb.rct):  # ビームと爆弾が衝突していたら
                        beams[j] = None#リストの要素一つずつに対して、爆弾と衝突判定、衝突した要素をNoneにする
                        bombs[i] = None
                        bird.change_img(6, screen)#こうかとんが喜ぶ
                        score.add_point()  #爆弾を打ち落としたらスコアアップ(1点)するループ
                        explosions.append(Explosion(bomb.rct.center)) #リストにappend

        explosions=[explosion for explosion in explosions if explosion.life > 0]#lifeが0より大きいExplosionインスタンスだけのリストにする。
        beams=[beam for beam in beams if beam is not None and check_bound(beam.rct)[0]]#noneでないものをビームリストからリストに更新,画面の範囲外に出たらリストから削除する
        bombs=[bomb for bomb in bombs if bomb is not None]#noneでないものを爆弾リストからリストに更新
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for beam in beams:#ビームの一つずつにupdate
            beam.update(screen)
        for bomb in bombs:#爆弾の一つずつにupdate
            bomb.update(screen)
        for explosion in explosions:#爆発の一つずつにupdate
            explosion.update(screen)
        score.update(screen)# updateメソッドを呼び出してスコアを描画するループ
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()


import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def mkdir(path):
    folder = os.path.isdir(path)

    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径
        print("---  new folder...  ---")
        print("---  OK  ---")

    else:
        print("---  There is this folder!  ---")

def save_excl(round,health,infector,cured,death):
    save_path = './result'
    mkdir(save_path)
    print('保存到'+save_path)
    result_excel = pd.DataFrame()
    result_excel["round"] = round
    result_excel["health"]=health
    result_excel["infector"]=infector
    result_excel["cured"] = cured
    result_excel["death"] = death
    result_excel.to_excel(save_path + '/result.xlsx')

class People(object):
    def __init__(self, count=1000, first_infected_count=3):
        self.count = count
        self.first_infected_count = first_infected_count
        self.init()
        self.round = []
        self.health = []
        self.infector = []
        self.recovery = []
        self.death = []

        self.suscept_rate=0.3 #恢复到易感的概率
        self.suscept_time=60 #60天后开始免疫消退
        self.safe_distance=3 #传染距离，大于该距离不被传染
        self.infecte_rate=0 #传染率，基于高斯分布，0为50%
        self.R0=20 #最大传染人数
        self.death_rate=0.001 #死亡率，默认千分之一
        self.move_width=10 #移动距离，默认最大移动10格
        # 地图大小设为1000
        # 95%的人阳后5-14天痊愈
        # 每天随机大约25%的人不移动


    def init(self):
        self._people = np.random.normal(0, 200, (self.count, 2)) #地图大小设为1000
        self.reset()

    def reset(self):
        self._round = 0
        self._status = np.array([0] * self.count)
        self._timer = np.array([0] * self.count)
        self.random_people_state(self.first_infected_count, state=2)

    def random_people_state(self, num, state=2):
        """随机挑选人设置状态
        """
        assert self.count > num
        # TODO：极端情况下会出现无限循环
        n = 0
        while n < num:
            i = np.random.randint(0, self.count)
            if self._status[i] == state:
                continue
            else:
                self.set_state(i, state)
                n += 1

    def set_state(self, i, state):
        self._status[i] = state
        # 记录状态改变的时间
        self._timer[i] = self._round

    def random_movement(self, width=1):
        """随机生成移动距离

        :param width: 控制距离范围
        :return:
        """
        return np.random.normal(0, width, (self.count, 2))

    def random_switch(self, x=0.):
        """随机生成开关，0 - 关，1 - 开

        x 大致取值范围 -1.99 - 1.99；
        对应正态分布的概率， 取值 0 的时候对应概率是 50%
        :param x: 控制开关比例
        :return:
        """
        normal = np.random.normal(0, 1, self.count)
        switch = np.where(normal < x, 1, 0)
        return switch

    @property
    def healthy(self):
        return self._people[self._status == 0]

    @property
    def infected(self):
        return self._people[self._status == 2]

    @property
    def cured(self):
        return self._people[self._status == 3]

    @property
    def dead(self):
        return self._people[self._status == 4]

    @property
    def suscept(self):
        return self._people[self._status == 1]

    def move(self, width=1, x=.0):
        movement = self.random_movement(width=width)
        # 限定特定状态的人员移动
        switch = self.random_switch(x=x)
        # movement[(self._status == 0) | switch == 0] = 0
        movement[(self._status == 3) |switch == 0] = 0
        self._people = self._people + movement

    def change_state(self):
        dt = self._round - self._timer
        # 必须先更新时钟再更新状态
        d = np.random.randint(5, 14)
        x = np.random.random(1)
        self._timer[(self._status == 2) & ((dt == d) | (dt > 14)) & (x<0.95)] = self._round
        self._status[(self._status == 2) & ((dt == d) | (dt > 14)) & (x<0.95)] += 1 #95%的人阳后5-14天痊愈



    def affect(self):
        # self.infect_nearest()
        self.susceptibility(rate=self.suscept_rate,time=self.suscept_time)
        self.infect_possible(rate=0.,safe_distance=self.safe_distance,R0=self.R0)
        self.dead_possible(rate=self.death_rate)


    def infect_nearest(self, safe_distance=3.0):
        """感染最接近的健康人"""
        for inf in self.infected:
            dm = (self._people - inf) ** 2
            d = dm.sum(axis=1) ** 0.5
            sorted_index = d.argsort()
            for i in sorted_index:
                if d[i] >= safe_distance:
                    break  # 超出范围，不用管了
                if self._status[i] > 0:
                    continue
                self._status[i] = 2
                # 记录状态改变的时间
                self._timer[i] = self._round
                break  # 只传 1 个

    def infect_possible(self, rate=0., safe_distance=3.0, R0=3):
        """按概率感染接近的健康人
        rate 的取值参考正态分布概率表，rate=0 时感染概率是 50%
        R0是传染人数，默认R0为3
        """
        count=0
        for inf in self.infected:
            dm = (self._people - inf) ** 2
            # d = dm.sum(axis=1) ** 0.5
            d = dm.sum(axis=1) ** 0.5
            sorted_index = d.argsort()
            for i in sorted_index:
                if d[i] >= safe_distance:
                    break  # 超出范围，不用管了
                if self._status[i] >1 :
                    continue
                if np.random.normal() > rate:
                    continue
                self._status[i] = 2
                # 记录状态改变的时间
                self._timer[i] = self._round
                count+=1
                if count>=R0:
                    break

    def susceptibility(self, rate=0.4,time=60):
        """40%的人在60天后恢复易感
        x 的取值为易感率
        """
        list=np.where(self._status == 3)
        list=list[0].tolist()
        for i in list:
            dt = self._round - self._timer[i]
        # 必须先更新时钟再更新状态
            # 痊愈情况
            if dt>time:# 痊愈者60天后易感
            #     self._status[i] = 0
            #     self._timer[i] = self._round
            # else:
            #     continue
                #设置一个随机数
                n = np.random.random(1)
                if n < rate:
                    continue
                else:
                    self._timer[i] = self._round
                    self._status[i] = 0  # 痊愈者60天后易感

    def dead_possible(self, rate=0.001):
        """参考死亡率为千分之1
        x 的取值为死亡率
        """
        list=np.where(self._status == 2)
        list=list[0].tolist()
        for i in list:
        #确诊的死亡
        #设置一个随机数
            n = np.random.random(1)
            if n > rate:
                continue
            else:
                self._status[i] = 4
                self._timer[i] = self._round


    def over(self):
        return len(self.healthy) == 0

    def report(self):
        #保存图像
        plt.cla()
        # plt.grid(False)
        p1 = plt.scatter(self.healthy[:, 0], self.healthy[:, 1], s=1, c='green')
        p2 = plt.scatter(self.infected[:, 0], self.infected[:, 1], s=1, c='red')
        p3 = plt.scatter(self.cured[:, 0], self.cured[:, 1], s=1, c='blue')
        p4 = plt.scatter(self.dead[:, 0], self.dead[:, 1], s=1, c='black')
        p5 = plt.scatter(self.suscept[:, 0], self.suscept[:, 1], s=1, c='aqua')

        plt.legend([p1, p2, p3, p4], ['healthy', 'infected', 'cured', 'death'], loc='upper right', scatterpoints=1)
        t = "Round: %s, Healthy: %s, Infected: %s, Cured: %s, Death: %s" % \
            (self._round, len(self.healthy), len(self.infected), len(self.cured), len(self.dead))
        plt.text(-700, 1000, t, fontsize=20, ha='left', wrap=True)
        savename="./save/Round_%s.jpg" % (self._round)
        plt.savefig(savename)
        plt.clf()
        #保存列表
        self.round.append(self._round)
        self.health.append(len(self.healthy))
        self.infector.append(len(self.infected))
        self.recovery.append(len(self.cured))
        self.death.append(len(self.dead))


    def update(self):
        """每一次迭代更新"""
        self.change_state()
        self.affect()
        self.move(width=self.move_width, x=0.66) # x函数为高斯分布，随机大约25%的人不移动
        self._round += 1
        self.report()
        print('Round_%s' % self._round)

    def save_result(self):
        """保存数据"""
        save_excl(round=self.round,health=self.health,infector=self.infector,cured=self.recovery,death=self.death)
        fig_result=plt.figure(figsize=(20, 20), dpi=100)
        plt.plot(self.round,self.health,'g-')
        plt.plot(self.round, self.infector, 'r-')
        plt.plot(self.round, self.recovery, 'b-')
        plt.plot(self.round, self.death, 'k-')
        plt.savefig("./save/results.jpg")

if __name__ == '__main__':
    np.random.seed(0)
    plt.figure(figsize=(20, 20), dpi=100)
    plt.ion()
    p = People(100000, 3)####这里填入初始人数，初始病人
    for i in range(365):
        p.update()
    p.save_result()

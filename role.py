class Role:
    def __init__(self, role_id, name, skills, health):
        self.role_id = role_id  # 角色的唯一标识符
        self.name = name        # 角色的名称
        self.skills = {skill.name: skill for skill in skills}  # 角色的技能字典
        self.health = health    # 角色的初始生命值
        self.is_chained = False  # 是否处于铁锁连环状态

    def trigger_skills(self, phase, game_state, player):
        """在特定阶段触发技能"""
        for skill in self.skills.values():
            if skill.trigger_phase == phase:
                if skill.can_activate(game_state, player):
                    skill.trigger(game_state, player)

    def use_skill(self, skill_name, target, game_state):
        """使用指定技能"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            if skill.can_activate(game_state, self, target):
                skill.trigger(game_state, self, target)

    def take_damage(self, damage, is_elemental=False):
        """角色受到伤害"""
        self.health -= damage
        print(f"{self.name} 受到了 {damage} 点伤害，剩余生命值: {self.health}")
        if self.health <= 0:
            print(f"{self.name} 被击败，退出游戏")
            return True  # 角色死亡
        if is_elemental and self.is_chained:
            self.pass_chain_damage(damage)
        return False  # 角色存活

    def pass_chain_damage(self, damage):
        """传递铁锁连环的伤害"""
        print(f"{self.name} 处于铁锁连环状态，传递 {damage} 点伤害")
        # 这里可以实现传递伤害的逻辑

    def chain_player(self):
        """将玩家设置为铁锁连环状态"""
        self.is_chained = True
        print(f"{self.name} 进入了铁锁连环状态")

    def unchain_player(self):
        """取消玩家的铁锁连环状态"""
        self.is_chained = False
        print(f"{self.name} 取消了铁锁连环状态")

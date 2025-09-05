"""
三国杀1v1全技能测试脚本
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app.models.game import Game, Card, CardType
from app.models.character import CharacterFactory
from models.skills import SkillManager, PaoXiao, KeJi, YingZi

def test_all_skills():
    """测试所有技能"""
    print("开始测试所有技能...")
    
    # 测试咆哮技能
    print("\n测试咆哮技能:")
    zhangfei = CharacterFactory.create_character("张飞")
    game = Game()
    # 添加玩家到游戏中
    game.add_player(zhangfei)
    player = game.players[0] if game.players else None
    
    if zhangfei.has_skill("咆哮"):
        print(f"{zhangfei.name} 拥有咆哮技能")
        # 设置游戏阶段为出牌阶段
        game.current_phase = "play"
        game.current_player = player
        # 尝试触发技能
        result = zhangfei.use_skill("咆哮", game, player)
        print(f"技能触发结果: {result}")
    else:
        print(f"{zhangfei.name} 不拥有咆哮技能")
    
    # 测试克己技能
    print("\n测试克己技能:")
    lumeng = CharacterFactory.create_character("吕蒙")
    game2 = Game()  # 创建新的游戏实例
    # 添加玩家到游戏中
    game2.add_player(lumeng)
    player2 = game2.players[0] if game2.players else None
    
    if lumeng.has_skill("克己"):
        print(f"{lumeng.name} 拥有克己技能")
        # 设置游戏阶段为弃牌阶段
        game2.current_phase = "discard"
        # 尝试触发技能
        result = lumeng.use_skill("克己", game2, player2)
        print(f"技能触发结果: {result}")
    else:
        print(f"{lumeng.name} 不拥有克己技能")
    
    # 测试英姿技能
    print("\n测试英姿技能:")
    zhouyu = CharacterFactory.create_character("周瑜")
    game3 = Game()  # 创建新的游戏实例
    # 添加玩家到游戏中
    game3.add_player(zhouyu)
    player3 = game3.players[0] if game3.players else None
    
    if zhouyu.has_skill("英姿"):
        print(f"{zhouyu.name} 拥有英姿技能")
        # 设置游戏阶段为摸牌阶段
        game3.current_phase = "draw"
        game3.current_player = player3
        # 尝试触发技能
        result = zhouyu.use_skill("英姿", game3, player3)
        print(f"技能触发结果: {result}")
    else:
        print(f"{zhouyu.name} 不拥有英姿技能")
    
    # 测试技能管理器
    print("\n测试技能管理器:")
    skill_manager = SkillManager()
    skill_manager.register_skill(PaoXiao())
    skill_manager.register_skill(KeJi())
    skill_manager.register_skill(YingZi())
    skill = skill_manager.get_skill("咆哮")
    if skill:
        print(f"成功获取技能: {skill.name}")
    else:
        print("未能获取技能")
    
    print("\n所有技能测试完成。")

if __name__ == "__main__":
    test_all_skills()
<template >
 <div id = "game" >
    <PlayerBoard v-for = "player in players": key = "player.player_id": player = "player"/>
    <Deck: deck = "deck" @ drawCard = "handleDrawCard"/>
    <DiscardPile: discardPile = "discardPile"/>
  </div >
</template >

<script >
export default {
    data() {
        return {
            players: [],        // 玩家信息
            deck: [],           // 牌堆
            discardPile: [],    // 弃牌堆
            currentPlayer: null // 当前回合的玩家
        }
    },
    methods: {
        handleDrawCard() {
            // 从服务器获取并更新状态
            },
        updateDisplay(newState) {
            // 根据新的游戏状态更新UI
          this.players = newState.players
          this.deck = newState.deck
          this.discardPile = newState.discardPile
          this.currentPlayer = newState.currentPlayer;
        }
    },
    mounted() {
        // 初始化游戏界面
        this.fetchGameState();
    }
};
</script >
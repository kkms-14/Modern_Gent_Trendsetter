var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        f1_tab: 1, // 1F 标签页控制
        f2_tab: 1, // 2F 标签页控制
        f3_tab: 1, // 3F 标签页控制
        total_count: 0, // 购物车总数量
        carts: [], // 购物车数据,
        username:'',
    },
    mounted(){
        // 获取购物车数据
        // this.get_carts();
        this.username=getCookie('username');
        console.log(this.username);
        this.render_carts();
        this.compute_total_count();

    },
    methods: {
        // 获取购物车数据
        get_carts(){
            var url = this.host+'/carts/simple/';
            axios.get(url, {
                    responseType: 'json',
                })
                .then(response => {
                    this.carts = response.data.cart_skus;
                    this.cart_total_count = 0;
                    for(var i=0;i<this.carts.length;i++){
                        if (this.carts[i].name.length>25){
                            this.carts[i].name = this.carts[i].name.substring(0, 25) + '...';
                        }
                        this.cart_total_count += this.carts[i].count;
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        render_carts(){
            // 渲染界面
            this.carts = JSON.parse(JSON.stringify(cart_skus));
            for(var i=0; i<this.carts.length; i++){
                if(this.carts[i].selected=='True'){
                    this.carts[i].selected=true;
                } else {
                    this.carts[i].selected=false;
                }
            }
            // 手动记录购物车的初始值，用于更新购物车失败时还原商品数量
            this.carts_tmp = JSON.parse(JSON.stringify(cart_skus));
        },
        // 计算商品总数量：无论是否勾选
        compute_total_count(){
            var total_count = 0;
            for(var i=0; i<this.carts.length; i++){
                total_count += parseInt(this.carts[i].count);
            }
            this.total_count = total_count;
        },
    }
});










// $(function(){
//     // 楼层选项卡
// 	var $tab = $('.subtitle a');
// 	var $content = $('.goods_list_con .goods_list');
//
// 	$tab.click(function(){
// 		var $index = $tab.index($(this));
// 		$(this).addClass('active').siblings().removeClass('active');
// 		$content.eq($index).addClass('goods_list_show').siblings().removeClass('goods_list_show');
// 	});
//
// 	// 获取并展示购物车数据
// 	get_cart();
// });
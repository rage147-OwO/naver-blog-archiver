---
title: c언어 반복문 while, do while
categories:
 - C
---
#c언어 반복문 while, do while : 네이버 블로그
<div class="wrap_rabbit pcol2 _param(1) _postViewArea221509095399" id="post-view221509095399">
<!-- Rabbit HTML --><div class="se-viewer se-theme-default" lang="ko-KR">
<!-- SE_DOC_HEADER_END -->
<div class="se-main-container">
<div class="se-component se-text se-l-default" id="SE-1d5f312d-4646-47e1-b947-a96220a3d007">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-f4b0022f-e235-48ad-9094-4a8abb4266cc" style=""><span class="se-fs- se-ff-" id="SE-9fc141e8-ab12-423f-946c-6a120846df4c" style="color:null;">c언어 반복문입니다. 보통 중간고사 범위가 여기까지 나와요</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-511047ee-05dc-42ae-a2dc-8c386a655c02" style=""><span class="se-fs- se-ff-" id="SE-dc10413e-4b69-4a82-8a9c-f7af6674bf47" style="color:null;">반복문은 크게 while과  for이 있습니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-291fca3d-f005-4f5a-b78b-d99239c25e68" style=""><span class="se-fs- se-ff-" id="SE-f975d40f-20d6-4863-a754-3becd6f7319c" style="color:null;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-7b591570-ce03-47a9-919c-a9fefe4783e9" style=""><span class="se-fs- se-ff-" id="SE-a217f7e2-7df8-4d4a-abb2-033f7b529a72" style="">while (true)</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-f963778a-6666-4321-8f75-ef42699e78c1" style=""><span class="se-fs- se-ff-" id="SE-6f768009-fda4-4705-9722-22fc39d070df" style="">{</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-9263e63d-f40c-4b0f-a7fc-9af8cbc65227" style=""><span class="se-fs- se-ff-" id="SE-140d7d26-04ba-4bc9-a285-f85c16ef71f2" style=""> printf("   ")</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-4ae4c362-ed17-498a-a280-845b5c054f79" style=""><span class="se-fs- se-ff-" id="SE-73f27d3f-cccf-4b19-a000-35dab59981b8" style="">}</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-43295660-b21a-4c86-83b3-f7889def1986" style=""><span class="se-fs- se-ff-" id="SE-9137f200-6bdc-44d8-bdaa-89a982133bb4" style="">while 뒤 괄호안에 있는 값이 사실(1)이 되면 아래의 식을 반복합니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-33867e5f-3b7a-4e20-9fef-15666dcb41eb" style=""><span class="se-fs- se-ff-" id="SE-f4ceb184-ea6d-4571-b0b0-6c5807b2659b" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-a339e3f6-bf29-460b-a24e-96fe7d21c67d">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
main(void) {
	int  i, n, sum;
	puts("정수를 입력하세요");
	scanf(" %d", &amp;n);
	i = 1;
	sum = 0;
	while (i &lt;= n) //입력한 수까지 1씩 올라가는 i
	{
		sum += i; //sum +=i 는 sum = sum+i, 기존의 sum에 i를 더함
		i++; //i를 1씩 올린다
	}
	printf("1부터 %d 까지의 합은 %d 입니다", n, sum);
	return 0;
	
}
</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-a339e3f6-bf29-460b-a24e-96fe7d21c67d"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-a27a60c9-599f-44b1-9580-951be8f2db8c">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-21e01c69-5452-435e-b745-5d8c8a85aea2" style=""><span class="se-fs- se-ff-" id="SE-9da646d9-7d3e-418d-a97c-3d888c03a474" style="">위 코드는 정수를 입력받고(a) i를 1로 초기화 한 후 1(i) 부터 입력한 정수(n)까지 i를 1씩 더한것을 sum에 더하는 코드입니다. </span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-555653cc-c42c-4a75-b050-7c930b713f34">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
main(void) {
	int  i, n, sum;
	puts("정수를 입력하세요");
	scanf(" %d", &amp;n);
	i = 0;
	sum = 0;
	while (i &lt;= n)
	{
		sum += i;
		i = i + 2;;
	}
	printf("0부터 %d까지 짝수의 합은 %d입니다 ", n, sum);
	return 0;
	
}
</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-555653cc-c42c-4a75-b050-7c930b713f34"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-08766681-c199-429a-a2d6-fdd95647a353">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-82e8fc4c-37fc-4f3a-96c7-c7c745f5268b" style=""><span class="se-fs- se-ff-" id="SE-f30c0c97-2644-47c1-bd25-9f5fa85f4451" style="">다음은 0부터 입력받은 n까지에 있는 짝수를 더하는 코드입니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-b01b9967-a6bb-4605-95ec-1028b5137c27" style=""><span class="se-fs- se-ff-" id="SE-aa17aaf9-dab3-43a8-80ae-ab13b90a9bda" style="">i는 0이였지만 i=i+2에 의해 반복시 2씩 올라가게 됩니다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-e14d0e6e-edf8-4373-977b-8f40a642b856" style=""><span class="se-fs- se-ff-" id="SE-77e2f771-2ff8-4734-80c6-13411ea6285d" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-a9d47083-fffd-4c8e-b716-e376c0aaf092">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
main(void) {
	int  i, n, sum;
	puts("5개의 정수를 입력하세요");
	i = 1;
	sum = 0;
	while (i &lt;= 5)
	{
		scanf("%d", &amp;n);
		sum =sum+ n;
		i++;
	}
	printf(" 5개의 합은 %d입니다 ",  sum);
	return 0;
	
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-a9d47083-fffd-4c8e-b716-e376c0aaf092"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-7b76723d-2518-4e67-9eaa-60e20f777c96">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-81c5bf50-bc34-476f-bd59-24af90c0daf9" style=""><span class="se-fs- se-ff-" id="SE-fe5ab069-1ac7-4636-9ed7-8b25479116b6" style="">다음은 입력받은 정수 5개를 더하는 코드입니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-a5c1516d-e3f4-4c33-9f59-a5f87a60b267" style=""><span class="se-fs- se-ff-" id="SE-e7bdbef1-5ea3-4c5c-86c8-5664fa5f736f" style="">scanf도 반복 안에 넣음으로써 입력도 반복을 시킬 수 있습니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-2ea39099-dbda-4528-bfda-be7e4ed64641" style=""><span class="se-fs- se-ff-" id="SE-627f27bb-a9bf-4870-8011-c6b2aebe1de6" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-08c9e32f-dbe2-4432-95b9-a6313f12d45a">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
main(void) {
	int  i, n, sum,average;
	n=0,
	sum = 0;
	i = 0;
	while (i&gt;=0) //i가 0보다 크면 종료한다
	{
		puts("성적을 입력하세요");
		scanf("%d", &amp;i); //i를 입력받는다
		sum += i; //입력받은 i를 sum에 더한다
		n++; //총 몇번 반복이 되었는지를 센다
	}  //반복에서 나가기 위해서는 마이너스 값을 입력한다
	sum = sum - i; //마지막에 저장된 i값은 마이너스므로 마지막 더한값을 뺀다
	n--; //이또한 같게 마지막에 반복된것은 마이너스를 더한 것이므로 반복으로 셀 수 없다
	average = sum / n;
	printf("학생의 수 %d\n총 성적의 합계%d\n성적의 평균은 %d ",n,sum,  average);
	return 0;
	
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-08c9e32f-dbe2-4432-95b9-a6313f12d45a"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-5de7d7d5-e2e1-4322-a74e-55d42a25be1c">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-665a869f-2dac-47b9-9e7c-04813825b8e2" style=""><span class="se-fs- se-ff-" id="SE-7a1e6ad7-d5ad-40a5-83d6-6cc8ef712eab" style="color:null;">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-ac49e648-9137-4899-ab2c-77aeb013d068">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
#include&lt;limits.h&gt; //INT_MAX를 쓸 수 있게 하는 헤더
main(void) {
	int  num, min_value = INT_MAX;
	puts("정수를 입력하세요\n종료는 컨트롤z3엔터 3번");
	while (scanf("%d",&amp;num) != EOF) //num을 입력받는다,!=EOF는 컨트롤 z가 아니면 실행한다라는 뜻
	{
		if (num &lt; min_value) //입력받은 num이 min_value보다 작으면
			min_value = num; //num을 min_value에 넣는다
	}
	printf("최소값은 %d ",min_value);
	return 0;
	
}
</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-ac49e648-9137-4899-ab2c-77aeb013d068"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-9cfc2fa8-4fab-402a-8c44-93871b8eb071">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-0fab473a-8328-4b71-b8bb-a635f1760cd3" style=""><span class="se-fs- se-ff-" id="SE-b0bd9bf5-6dfa-4843-9b63-7ea74c3552b7" style="color:null;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-ed940e1d-31d7-447e-820e-1c4658fcc896" style=""><span class="se-fs- se-ff-" id="SE-5f1f3ddf-c3bc-4993-9800-68bb1b878cb6" style="color:null;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-0d9fe8ef-7671-426c-bd6d-f0d1d65edbd2" style=""><span class="se-fs- se-ff-" id="SE-e6624c71-3b34-4f2c-ac8e-589f58f51c5f" style="color:null;">아래의 예제는 랜덤한 숫자를 만들어 숫자를 맞추는 코드이다</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-e738dd35-7f33-4dd0-927c-ae161f1f2454">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
#include&lt;stdlib.h&gt;
#include&lt;time.h&gt;
int main() {
	int i = 0;
	int o;
	srand(time(NULL));
	o = rand() % 45 + 1; //45까지의 랜덤한 수를 o로 지정한다


	do
	{
		puts("추측 숫자를 입력하세요");
		scanf(" %d", &amp;i);
		if (o &lt; i)
			puts("추측 숫자보다 작습니다");
		if (o &gt; i)
			puts("추측 숫자보다 큽니다");
	} while (i != o);

	printf("맞췄습니다 숫자는 %d 입니다\n", i);
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-e738dd35-7f33-4dd0-927c-ae161f1f2454"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-689d688d-dcc0-4a87-b86d-af253d0d0302">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-5a61b587-33e5-4c2a-bc8a-50f8062bc38e" style=""><span class="se-fs- se-ff-" id="SE-8ed31951-e61d-4911-9911-9551b82b5a78" style="color:null;">do while은 일다나 실행하고 조건에 참이면 계속 반복하는 반복문이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-94092a23-0f23-4304-8702-a4d34f8519d7" style=""><span class="se-fs- se-ff-" id="SE-c22fb03a-d56b-4dd7-99c9-65c868caf57f" style="color:null;">위 코드에서는 45까지 랜덤한 수 o와 입력한 수 i가 같지 않으면 반복하게 되어 있다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-90df7794-437f-43fa-9149-762d21105d8b" style=""><span class="se-fs- se-ff-" id="SE-e81ea59c-7991-42bd-8344-445fa1879c6a" style="color:null;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-d1e86ed3-f5f7-4501-b7ab-e18968789287" style=""><span class="se-fs- se-ff-" id="SE-caa828e3-8864-450e-bd8a-3d6c5b18d442" style="color:null;">고로 o와 i가 같게 되면 반복이 끝나고 i를 출력하게 된다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-674bfe3e-c857-4b22-8aa5-d0e01087ac1e" style=""><span class="se-fs- se-ff-" id="SE-9a531f85-1e2c-4a72-b169-a0fb5314460f" style="color:null;">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> </div>
</div>
</div>
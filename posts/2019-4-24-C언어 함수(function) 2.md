---
title: C언어 함수(function) 2
categories:
 - C
---
#C언어 함수(function) 2 : 네이버 블로그
<div class="wrap_rabbit pcol2 _param(1) _postViewArea221521725259" id="post-view221521725259">
<!-- Rabbit HTML --><div class="se-viewer se-theme-default" lang="ko-KR">
<!-- SE_DOC_HEADER_END -->
<div class="se-main-container">
<div class="se-component se-text se-l-default" id="SE-40f8aa43-851d-40f7-97e6-4f924681ab81">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-085d00d3-4c28-4364-8ea4-b9878ce1520c" style=""><span class="se-fs- se-ff-" id="SE-e8a9f48e-c1ee-48e5-9f64-e03c35a3397c" style="">c언어의 함수는 기본적으로</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-f1f91a76-75b7-4289-9dd7-c4764074ab36" style=""><span class="se-fs- se-ff-" id="SE-ed082aa0-17f8-468d-80a7-a1785a5a57f3" style="">반환 자료형(void, int, double...) 함수이름 인수목록 {함수몸체} 의 구조로 구성된다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-7d68cab0-6d95-4603-8e5e-08daf0306646" style=""><span class="se-fs- se-ff-" id="SE-544d358a-0302-4203-a033-971f6376416a" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-adfabbfa-ab41-4c7a-a23a-7b52ffe42699" style=""><span class="se-fs- se-ff-" id="SE-d5415402-3fb9-4ea6-9a28-97677032494f" style="">함수는 사용자 정의 함수와 라이브러리 함수가 있는데</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-09928420-15c8-4db6-a0f1-4090778af87f" style=""><span class="se-fs- se-ff-" id="SE-171c0327-2e01-42d9-b8a7-bff160ba18ae" style="">라이브러리 함수는 printf나 scanf처럼 헤더 파일에 정의되어있는 함수이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-23143dcc-b414-4e15-8503-c09d0de57e3a" style=""><span class="se-fs- se-ff-" id="SE-87dab270-7bc1-4ede-9ee5-f61389052fc4" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-8262fb68-34b3-4aad-9824-83f061c33bbf" style=""><span class="se-fs- se-ff-" id="SE-d96a86c9-ee25-4ceb-a0ea-d4f0438f16ad" style="">오늘 다루는 함수는 사용자 정의 함수이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-a5296187-08b0-43a4-a64f-46af79ce95ec" style=""><span class="se-fs- se-ff-" id="SE-6f2607ba-e9c5-493a-a2cd-52ca068ce9aa" style="">사용자 정의 함수를 쓰는 이유는</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-4b0ee6e3-4d12-4f96-8fd3-f117fa27e023" style=""><span class="se-fs- se-ff-" id="SE-1d4e7a40-8384-4542-8100-cb748ddaf9fb" style="">1. 불필요한 중복 코드를 줄일 수 있다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-60417a28-e62c-4a5b-ba69-b74f726ad3ad" style=""><span class="se-fs- se-ff-" id="SE-6c507642-0643-4f95-902e-197d18482bab" style="">2. 체계적이고 간결하게 할 수 있다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-280bfa73-0252-4005-9ece-5c7425aee9e5" style=""><span class="se-fs- se-ff-" id="SE-46edf725-ff5e-44b9-9259-cdfd08d1b1ef" style="">3. 함수 내의 변수를 선언해 변수 간의 중복을 피할 수 있다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-b0c63f4d-f823-415c-ba93-77bb7e181d3c" style=""><span class="se-fs- se-ff-" id="SE-6add96dc-f4e6-441a-bb25-164234d2e9ff" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-d9cf5ea6-11ae-4a96-ad36-d4d175b62ac2" style=""><span class="se-fs- se-ff-" id="SE-93ec9695-cd1c-4900-aa50-2109bd147bbb" style="">아래 예제들을 보자</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-efca9aa8-1c28-4ab0-8f0c-109e75b8ec01">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
void happy_birthday(){
	printf("생일축하합니다\n");
}
int main() {
	happy_birthday(); //void는 함수()형임을 기억하자
	happy_birthday();
	printf("사랑하는 학생의 ");
	happy_birthday();
	return 0;
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-efca9aa8-1c28-4ab0-8f0c-109e75b8ec01"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-ed6c3c1b-941a-4ae4-b2c4-79264c991d29">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-f29bb2dc-0570-4d68-9a56-652fa389f645" style=""><span class="se-fs- se-ff-" id="SE-a9f4f462-dca9-4777-adc5-7cb2c0333880" style="">void happy_birthday()는 입력(전달인자)가 없고 반환도 없는 함수이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-95101baf-f55d-43ce-8cb7-d7e55ddd6ed1" style=""><span class="se-fs- se-ff-" id="SE-e3685d96-3615-4865-a2f8-f860c4f88f11" style="">여기서 반환은 return 값이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-ef91af2b-7f5f-4939-868c-9501002594da" style=""><span class="se-fs- se-ff-" id="SE-c00d2b37-2f39-42b7-b89e-ff8d0b98cc28" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-8bc650b4-a0dd-4578-ac51-71bdbfe5d2a5" style=""><span class="se-fs- se-ff-" id="SE-9b05c26c-0330-46ff-8fd0-29554db926b0" style="">즉 printf로 인해 출력된다 해도 반환은 없다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-d2476c82-d186-4d25-829b-199bcc88ee8e" style=""><span class="se-fs- se-ff-" id="SE-c864465a-f3d1-4c85-b45f-307673231ca7" style="">입력과 반환의 의도에 따라 자료형을 적절히 선택하자.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-6a106cfb-1714-4fe7-9012-116c40f2c31e" style=""><span class="se-fs- se-ff-" id="SE-7b20d9db-8af5-4ec6-ac47-942c0add24f6" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-2df2a1fe-d732-44e8-9634-2e38d90cb92f">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
int add(int x, int y){
	return x + y;
}
int main() {
	int x, y;
	scanf("%d%d", &amp;x, &amp;y);
	printf("%d", add(x, y));
	return 0;
}
</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-2df2a1fe-d732-44e8-9634-2e38d90cb92f"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-564736fc-556f-4f89-a2a1-1e8f7b29697f">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-badff828-4dfc-4f0d-95f4-83693ad4e9d8" style=""><span class="se-fs- se-ff-" id="SE-42298666-7089-40e1-b58b-76734f8bc058" style="">add라는 함수는 add(  x ,y  )형태로 입력받아</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-cb7be066-0e5d-4b9d-b861-cf3e50bdc654" style=""><span class="se-fs- se-ff-" id="SE-555fef95-88b4-4ada-90e7-a1412c41cf18" style="">x+y를 반환하는 함수이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-4d2c4f08-2d3d-4644-99c7-aaaebbfdae7e" style=""><span class="se-fs- se-ff-" id="SE-ed5af18f-fccc-44c6-9948-7c4dc6d78c68" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-a604a049-3a2b-4945-9ccc-51546916d8c2" style=""><span class="se-fs- se-ff-" id="SE-c35d88a2-5b22-41fd-afcb-ab0573a76844" style="">즉 x+y는 add(x,y)와 같다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-6c34d3fb-a7aa-4b87-9e0d-8e58be283762" style=""><span class="se-fs- se-ff-" id="SE-4014a909-47df-40e2-b896-52d37ef14b3f" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-e5e19a3f-7627-42da-a5e7-e882a7fb0487">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
int fact(int n) {
	int sum = 1;
	for (int i = 1; i &lt;= n; i++)
	{
		sum *=i;
	}
	return sum;
}

int main() {
	int a;
	scanf("%d", &amp;a);
	printf("%d", fact(a));
	return 0;
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-e5e19a3f-7627-42da-a5e7-e882a7fb0487"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-2fea5cb8-a669-4161-a713-26e6746e2797">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-afbc84a2-761f-4801-b8b9-80b2563a2d28" style=""><span class="se-fs- se-ff-" id="SE-c626f63e-d8dd-4da4-a9e8-888c5de10489" style="">fact함수는 입력받은 int형 n의 팩토리얼을 int형 sum으로 반환하는 함수이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-9364e211-f3a1-48c1-886a-089ac0cb3da7" style=""><span class="se-fs- se-ff-" id="SE-f0ccc8c3-8de4-4c1b-a656-942eb57932f3" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-ae9e630e-5805-4c51-a433-23c768132a0f" style=""><span class="se-fs- se-ff-" id="SE-b7fe2ece-3db1-42df-a9bc-f4dea572dd45" style="">함수를 적절히 사용하기 위해서는 함수의 기능이 무엇인지, 무엇을 반환하는지 생각하는 것이 중요하다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-dcf7f40b-26f4-4fdd-8739-f90ff49de57e" style=""><span class="se-fs- se-ff-" id="SE-4d436ef3-2e38-4363-b67d-6e7c82c00b5d" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-b623d0ab-8eb0-477e-9acb-80dc3226140c">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
char op(); //함수 선언만 하고 내용은 아래에 적는다(함수원형)
double ch(char o);
int main() {
	double result;
	printf("%f", ch(op())); //ch 함수의 입력을 op의 출력값으로 놓을 수 있다.
}
char op() {
	puts("'c' 섭씨온도에서 화씨온도 변환");
	puts("'f' 화씨온도에서 섭씨온도 변환");
	puts("'q' 종료");
	char o;
	scanf(" %c", &amp;o);
	return o;
}
double ch(char o) {
	double temp;
	scanf("%lf", &amp;temp);
	switch (o)
	{
	case 'c':
		return 9.0 / 5.0*temp + 32;
	case 'f':
		return (temp - 32.0)*5.0 / 9.0;
	default:
		break;
	}
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-b623d0ab-8eb0-477e-9acb-80dc3226140c"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-2ce65db5-27f8-4410-899c-71f7d13896f0">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-af21fd06-7dbf-4203-a528-0e1aebfb3910" style=""><span class="se-fs- se-ff-" id="SE-6fa359d4-e81b-4248-84d6-83f0f93eb7a7" style="">위 코드에서는 새로운 것이 2가지 나온다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-126f0894-8ed7-4458-94d5-ab98d832dafa" style=""><span class="se-fs- se-ff-" id="SE-936cec60-8f8c-420f-99e0-3dd88ae61029" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-abaf4865-df28-4559-baad-2fc466880510" style=""><span class="se-fs- se-ff-" id="SE-ae4afb17-0c53-4f3c-960a-d415707c686a" style="">1. 함수원형</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-991b1e63-d21e-42ce-b637-3d069ec5abee" style=""><span class="se-fs- se-ff-" id="SE-efe9619e-6e81-4904-9d5d-e8ed601f31a8" style="">코드의 위에서는 선언만 하고 아래에 함수 내용을 써놓 수 있다,</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-272fca51-3f86-41c9-a125-08893308d431" style=""><span class="se-fs- se-ff-" id="SE-6024828a-7307-434d-a862-34af0365066b" style="">2.함수의 입력을 함수의 출력으로 놓을 수 있다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-2db862dc-2303-4424-9d67-b84f6cfece24" style=""><span class="se-fs- se-ff-" id="SE-de60a6e2-113b-452c-af75-4e7d638843b5" style="">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-48e92331-5d9e-4529-b7b9-a41290afe8d1">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
int com(int n, int r);
int fact(int n);
int get(void);
int main(void) {
	int n, r;
	n = get();
	r = get();
	printf("C(%d, %d) =%d \n", n, r, com(n, r));
	return 0;
}
int com(int n, int r) {
	return (fact(n) / (fact(r)*fact(n - r))); //함수의 반환을 입력으로 쓸 수 있다.
}
int fact(int n) {
	int i;
	int result = 1;
	for (i = 1; i &lt;= n; i++)
		result *= i;
	return result;
}
int get(void) {
	int n;
	puts("정수를 입력하세요 : ");
	scanf("%d", &amp;n);
	return n;
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-48e92331-5d9e-4529-b7b9-a41290afe8d1"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-ac24ae00-4349-46ec-bb9b-ea93b56db870">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-978e1e81-5afb-4e94-b10a-7279e0e29c09" style=""><span class="se-fs- se-ff-" id="SE-a60854cf-c5e3-4c56-bdcc-08218d624aa3" style="">위 코드는 조합(</span><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-d135e086-3c2a-4947-977f-c8edddb12929" style="color:#222222;background-color:#ffffff;">combination)을 구하는 코드입니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-2c1a95dc-862e-4aee-a88d-87f443fb8600" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-a2dd5d77-29a7-4b57-b5a6-54e73efff8fc" style="color:#222222;background-color:#ffffff;">com,fact,get 함수가 있는데</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-267c4992-eaee-470c-85ab-d2c46d261d65" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-f48dd903-900e-47ec-85fd-c05aa05c85e8" style="color:#222222;background-color:#ffffff;">get함수는 scanf로 받은 값을 반환시키는 역할을 합니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-b5e423e1-9d61-4185-8f13-d4264185bb4d" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-a2f0bc31-336a-42a5-87c1-cd4c68ff1431" style="color:#222222;background-color:#ffffff;">fact 함수는 입력된 수의 팩토리얼을 구한 후 반환합니다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-bc6bccba-a73a-4ac9-a1e4-f731345542ce" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-44cca4dc-41cc-4738-b5c7-3fd202d46426" style="color:#222222;background-color:#ffffff;">com 함수는 </span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-formula se-l-default" id="SE-e91336b2-e9c0-4da4-b9e2-8ce6509bf887">
<div class="se-component-content">
<div class="se-section se-section-formula se-l-default se-section-align-">
<div class="se-module se-module-formula __se_formula"></div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_formula", "id" :"SE-e91336b2-e9c0-4da4-b9e2-8ce6509bf887", "data" : { "fontSizeCode" : "fs15", "html": "\u003Cdiv class=\"lama-viewer\" style=\"font-size: 15px;\"\u003E\u003Cdiv class=\"mq-math-mode-wrapper\"\u003E\u003Cdiv class=\"mq-math-mode\" style=\"display: block;\"\u003E\u003Cspan class=\"mq-selectable\"\u003E$\\frac{n!}{r!\\left(n-r\\right)!}$\u003C/span\u003E\u003Cspan class=\"mq-root-block mq-hasCursor\"\u003E\u003Cspan class=\"mq-fraction mq-non-leaf\"\u003E\u003Cspan class=\"mq-numerator\"\u003E\u003Cvar\u003En\u003C/var\u003E\u003Cspan\u003E!\u003C/span\u003E\u003C/span\u003E\u003Cspan class=\"mq-divider\"\u003E\u003C/span\u003E\u003Cspan class=\"mq-denominator\"\u003E\u003Cvar\u003Er\u003C/var\u003E\u003Cspan\u003E!\u003C/span\u003E\u003Cspan class=\"mq-non-leaf\"\u003E\u003Cspan class=\"mq-scaled mq-paren\" style=\"transform: scale(0.993237, 1.15942);\"\u003E(\u003C/span\u003E\u003Cspan class=\"mq-non-leaf\"\u003E\u003Cvar\u003En\u003C/var\u003E\u003Cspan class=\"mq-binary-operator\"\u003E−\u003C/span\u003E\u003Cvar\u003Er\u003C/var\u003E\u003C/span\u003E\u003Cspan class=\"mq-scaled mq-paren\" style=\"transform: scale(0.993237, 1.15942);\"\u003E)\u003C/span\u003E\u003C/span\u003E\u003Cspan\u003E!\u003C/span\u003E\u003C/span\u003E\u003Cspan style=\"display:inline-block;width:0\"\u003E​\u003C/span\u003E\u003C/span\u003E\u003Cspan class=\"mq-cursor\"\u003E​\u003C/span\u003E\u003C/span\u003E\u003C/div\u003E\u003C/div\u003E\u003C/div\u003E", "thumbnail" : {"@ctype":"thumbnail","src":"https://blogfiles.pstatic.net/MjAxOTA0MjRfMTM5/MDAxNTU2MDk2NzE1NDA2.4GAoOwqwU_WJRRuG_x7xX9OIFt_I1InLcFe1OlOiRtwg.v8OI4c7qfzofO5D5Ok0OJMaQsWdGVetTy3aPTjjiqPgg.PNG.dls32208/modifiedImg0.png","width":102,"height":81} }}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-57443b46-53c3-4cd8-a661-51c3910049a5">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-5d26fe4c-3db1-460b-8f5f-463ccdefa358" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-1490fe85-2d1b-4984-b033-78c59c2f3359" style="color:#222222;background-color:#ffffff;">을 계산하는 함수입니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-e866d02e-29cf-4203-84f1-d82baa05dac1" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-1ea29487-7523-4528-a745-196823edfce5" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-3443836d-d8fa-4030-937e-5af45e0edf40" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-e6c48956-e2d5-4b0d-994d-0ca521d4baed" style="color:#222222;background-color:#ffffff;">위 코드의 중요한 사실은 함수의 반환값을 새로운 함수의 입력값으로 쓸 수 있는 것입니다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-fa67674f-9644-4f6b-b96a-32b3d55e60a4" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-6018d2a8-fe5d-4b5f-abe8-e1c072ce9781" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-385f9719-1cd2-4088-80b6-f927b20dc9d5" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-ba30b7ea-8e4f-4a01-8830-dab84bf0e85d" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> <div class="se-component se-code se-l-default" id="SE-a995bc90-2dcb-4b2e-b2f1-0ad6679a26af">
<div class="se-component-content">
<div class="se-section se-section-code se-l-default">
<div class="se-module se-module-code se-fs-fs13">
<div class="se-code-source">
<div class="__se_code_view language-javascript">#include&lt;stdio.h&gt;
int is_prime(int n);
int get(void);
void result(int a);

int main(void) {
	result(is_prime(get())); //get실행 후 반환값을 is_prime에 넣고 그 반환값이 result로 들어간다
}

int is_prime(int n) {
	for (int i = 2; i &lt; n; i++)
		if (n%i == 0) {
			printf("약수 %d\n", i);
			return 0;

		}
	return 1;
}
int get(void) {
	int a;
	scanf("%d", &amp;a);
	return a;
}
void result(int a) {
	a ? puts("소수입니다") : puts("소수가 아닙니다");
}</div>
</div>
</div>
</div>
</div>
<script class="__se_module_data" data-module='{"type":"v2_code", "id" : "SE-a995bc90-2dcb-4b2e-b2f1-0ad6679a26af"}' type="text/data"></script>
</div> <div class="se-component se-text se-l-default" id="SE-19b242d4-a941-49ac-9a32-ef0923a7f204">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text"><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-7df4dbdb-3ec8-4efe-af49-c1829832b3aa" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-69140582-b500-4c99-bddf-9efbf98fdb5e" style="color:#222222;background-color:#ffffff;">위 코드는 입력받은 정수가 소수인지 판별하는 프로그램이다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-bd217472-2193-407d-9d72-8bbf3be105d5" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-200157d6-097e-421d-a029-5b74e3dba817" style="color:#222222;background-color:#ffffff;">위 함수는 get,is_prime,result가 있다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-7982ad2b-d5d9-43bb-8f12-7f70d9f995af" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-f12c2b0e-939f-4597-9938-961b9b935e9f" style="color:#222222;background-color:#ffffff;">get은 void를 인수로 가지고 int형을 반환한다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-9d916a9b-e159-463c-a8e9-87ae4367cc89" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-19e6b01c-64fd-4b0f-b4a0-6b89892093f1" style="color:#222222;background-color:#ffffff;">반환하는 값은 scanf한 a이다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-79fc09a6-b791-42df-b3b4-38005daed778" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-cc6e5e3f-75bd-4c6a-8143-d20ddf036506" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-32c1d8e6-d76a-43a0-b8d3-5cfccd8de16e" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-1b3dae6b-94f1-4d5f-b0df-d87ee4c8f5bf" style="color:#222222;background-color:#ffffff;">is_prime은 int를 인수로 가지고 int헝을 반환한다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-56884af0-54df-477f-8bd4-f1023a14952d" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-c45681d9-7bd8-4d8b-9991-e46235bffb78" style="color:#222222;background-color:#ffffff;">i가 1씩 올라가며 </span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-5d0fda82-d6b5-47a8-9348-e404880459f7" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-58c2e670-51bd-4254-8879-77fa7e6ca5cf" style="color:#222222;background-color:#ffffff;">만약(if) 인수 n을 i로 나눴을때 나머지가 0이라면, 즉 약수가 있다면 그n을 출력한다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-8a33a20a-db53-47cb-9e7b-7aa43adeba17" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-49a4ef57-7219-43ff-b575-cf26fcd0db0a" style="color:#222222;background-color:#ffffff;">그리고 0을 반환한다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-437a60b3-414d-402d-a17f-e80d4fb3567f" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-6ba8f046-01f1-4db9-b0b5-72fd27be348e" style="color:#222222;background-color:#ffffff;">나눴을때 나머지가 0이되는 값이 없으면(약수가 없으면) 0을 반환한다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-ddc75304-5860-4719-848e-fedf25e41b82" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-dd8b5bfb-a7a6-45e2-98be-bdd22d126ae1" style="color:#222222;background-color:#ffffff;">is_prime에서 반환받은 값은 result의 인수가 되는데 인수에 따라 소수인지 아닌지를 판별한다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-1824e42e-99d4-4709-a839-bb152b9aa624" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-4c53d409-bd97-414e-8fe1-51a5fcf73abb" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-042e7640-b414-4793-8aab-1613629cfb05" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-f8552f7d-2ef1-488e-bf45-917a12452d35" style="color:#222222;background-color:#ffffff;">함수같은 경우에는 다시 말하지만 어떤 형태를 인수,반환 형태로 갖느냐가 매우 중요한 것 같다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-b2eae8ca-6601-4674-b867-20b1c631d8da" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-5a65f514-891a-4100-abe6-93ff7102ee04" style="color:#222222;background-color:#ffffff;">또 어느 기능적으로 함수를 나눌지에 따라 좋은 코드가 될 수 있고 나쁜 코드가 될 수 있다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-d07e89da-27ce-405e-85d4-a9b6e74cec24" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-648462c7-c0b0-4690-9a3c-0ac8b156e7f2" style="color:#222222;background-color:#ffffff;">개발자의 센스가 매우 중요한 것 같은 기능이다. </span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-54e94634-f32f-4571-a23a-e317278501bc" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-6586123e-9157-4598-b5b1-8a480d272b9f" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-876fd7ea-6b58-424e-a2fc-bbe7680478a2" style=""><span class="se-fs-fs16 se-ff-system se-style-unset" id="SE-0df66013-a2bc-4aef-9097-d84b18f44333" style="color:#222222;background-color:#ffffff;">​</span></p><!-- } SE-TEXT --></div>
</div>
</div>
</div> </div>
</div>
</div>
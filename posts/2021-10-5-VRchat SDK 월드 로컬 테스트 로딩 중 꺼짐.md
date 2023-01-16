---
title: VRchat SDK 월드 로컬 테스트 로딩 중 꺼짐
categories:
VRchat
---
#VRchat SDK 월드 로컬 테스트 로딩 중 꺼짐 : 네이버 블로그
<div class="wrap_rabbit pcol2 _param(1) _postViewArea222527879082" id="post-view222527879082">
<!-- Rabbit HTML --><div class="se-viewer se-theme-default" lang="ko-KR">
<!-- SE_DOC_HEADER_END -->
<div class="se-main-container">
<div class="se-component se-text se-l-default" id="SE-4227188d-0f86-4aeb-b089-7e48271ca038">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text">
<!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-b2d6464c-932f-49b2-8f02-7602fe46f899" style=""><span class="se-fs- se-ff-" id="SE-2b83d371-4aa3-4b78-9698-a55e13c4a82c" style="">필자는 VRchat SDK3 에서 로컬 테스트를 하는 중 꺼지는 문제가 생겼었다</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-f697a0ba-ffd7-4b8b-80bf-6df6c3c33e41" style=""><span class="se-fs- se-ff-" id="SE-3369f78d-97e4-47ad-bb2b-afdcce7e51d8" style="">​</span></p><!-- } SE-TEXT -->
</div>
</div>
</div>
</div> <div class="se-component se-image se-l-default" id="SE-f4c74234-52c4-4075-aa67-9918433d38d4">
<div class="se-component-content se-component-content-fit">
<div class="se-section se-section-image se-l-default se-section-align-">
<div class="se-module se-module-image" style="">
<a class="se-module-image-link __se_image_link __se_link" data-linkdata='{"id" : "SE-f4c74234-52c4-4075-aa67-9918433d38d4", "src" : "https://postfiles.pstatic.net/MjAyMTEwMDVfMjMx/MDAxNjMzNDQ0Mjk4ODk3.CsZ2wmEaTKsEM-nC3xM_Ubw_ZZQmNdh4jWjhcxmO0BMg.qJc5AjWF2pnX-QtXN3pMe3F6PzZrHFZN8umQPAIboiUg.PNG.dls32208/%EB%8F%84%EC%9B%80.png", "originalWidth" : "1212", "originalHeight" : "516", "linkUse" : "false", "link" : ""}' data-linktype="img" href="#" onclick="return false;" style="">
<img alt="" class="se-image-resource" data-height="295" data-lazy-src="https://postfiles.pstatic.net/MjAyMTEwMDVfMjMx/MDAxNjMzNDQ0Mjk4ODk3.CsZ2wmEaTKsEM-nC3xM_Ubw_ZZQmNdh4jWjhcxmO0BMg.qJc5AjWF2pnX-QtXN3pMe3F6PzZrHFZN8umQPAIboiUg.PNG.dls32208/%EB%8F%84%EC%9B%80.png?type=w966" data-width="693" src="https://postfiles.pstatic.net/MjAyMTEwMDVfMjMx/MDAxNjMzNDQ0Mjk4ODk3.CsZ2wmEaTKsEM-nC3xM_Ubw_ZZQmNdh4jWjhcxmO0BMg.qJc5AjWF2pnX-QtXN3pMe3F6PzZrHFZN8umQPAIboiUg.PNG.dls32208/%EB%8F%84%EC%9B%80.png?type=w80_blur">
</img></a>
</div>
</div>
</div>
</div>
<div class="se-component se-text se-l-default" id="SE-f38ab2a7-9bdb-49ab-9949-04ec85c2c484">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text">
<!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-479217cc-3e73-4ee3-a0a0-620dfc9c52f9" style=""><span class="se-fs- se-ff-" id="SE-4ea6a850-eae3-4596-8feb-d76072fc0cc8" style="">로그의 스크린샷.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-1b748cc1-663d-47ce-9cc3-6ccd228f2f5e" style=""><span class="se-fs- se-ff-" id="SE-06484944-a09d-42f2-9c9b-1be67111d296" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-8081ed26-b2ab-4f25-bff9-3bb92f796a2b" style=""><span class="se-fs- se-ff-" id="SE-ab43e85e-8bf6-47c1-87b5-0b2c74a0db17" style="">로딩 화면 중 꺼진다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-d07ca401-eb6f-4ff2-b872-b82f71dac4db" style=""><span class="se-fs- se-ff-" id="SE-c00afc7f-ec28-4da7-8d8c-e31192305d80" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-f00e42c0-e9a9-4051-a542-1e28db044e91" style=""><span class="se-fs- se-ff-" id="SE-4d6bb205-ed66-456d-8b04-e2a78b863db4" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-e6d75113-63e8-484a-8e28-0508eb4ee409" style=""><span class="se-fs- se-ff-" id="SE-7ebbf75a-f6ef-473f-b5ca-765a723d7ab7" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-df4b91fc-885e-4c6b-9f03-4366c921ffe5" style=""><span class="se-fs- se-ff-" id="SE-7c0529a7-50b6-485e-b455-bca7d937482d" style="">해결방법은</span></p><!-- } SE-TEXT -->
</div>
</div>
</div>
</div> <div class="se-component se-image se-l-default" id="SE-bde93b67-d7f6-45cb-b0ad-eaedaa4e9ac5">
<div class="se-component-content se-component-content-normal">
<div class="se-section se-section-image se-l-default se-section-align-" style="max-width:550px;">
<div class="se-module se-module-image" style="">
<a class="se-module-image-link __se_image_link __se_link" data-linkdata='{"id" : "SE-bde93b67-d7f6-45cb-b0ad-eaedaa4e9ac5", "src" : "https://postfiles.pstatic.net/MjAyMTEwMDVfMjI1/MDAxNjMzNDQ0Mjg3Mjcx.O5QVwEUqlvKH1-1cuhbKQCz5xFMzNbq6f6KW53P30zgg.NS5D2hWs3IHvM9R0pD1xnRYSKx7c2TNwTLn3K3VYNlAg.PNG.dls32208/%EC%BA%A1%EC%B2%98.PNG", "originalWidth" : "550", "originalHeight" : "449", "linkUse" : "false", "link" : ""}' data-linktype="img" href="#" onclick="return false;" style="">
<img alt="" class="se-image-resource" data-height="449" data-lazy-src="https://postfiles.pstatic.net/MjAyMTEwMDVfMjI1/MDAxNjMzNDQ0Mjg3Mjcx.O5QVwEUqlvKH1-1cuhbKQCz5xFMzNbq6f6KW53P30zgg.NS5D2hWs3IHvM9R0pD1xnRYSKx7c2TNwTLn3K3VYNlAg.PNG.dls32208/%EC%BA%A1%EC%B2%98.PNG?type=w966" data-width="550" src="https://postfiles.pstatic.net/MjAyMTEwMDVfMjI1/MDAxNjMzNDQ0Mjg3Mjcx.O5QVwEUqlvKH1-1cuhbKQCz5xFMzNbq6f6KW53P30zgg.NS5D2hWs3IHvM9R0pD1xnRYSKx7c2TNwTLn3K3VYNlAg.PNG.dls32208/%EC%BA%A1%EC%B2%98.PNG?type=w80_blur">
</img></a>
</div>
</div>
</div>
</div>
<div class="se-component se-text se-l-default" id="SE-40e528fc-8abd-48c3-8cd7-be48cb427f5c">
<div class="se-component-content">
<div class="se-section se-section-text se-l-default">
<div class="se-module se-module-text">
<!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-37503418-78b6-431f-971f-05d254719674" style=""><span class="se-fs- se-ff-" id="SE-5ac52777-0b9d-4ed7-845e-1b4fca897974" style="">SDK의 세티에서 맨 아래 VRchat Client를 들어가</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-7ec072a3-78a3-4232-97c7-16baf1243364" style=""><span class="se-fs- se-ff-" id="SE-c4673828-ef09-4d20-ba4e-85fce89f8443" style="">Edit에서 올바른 VRchat.exe 파일을 연결 해 주면 됀다.</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-c4e96da7-7798-4461-8108-0fe1d9d4b6a0" style=""><span class="se-fs- se-ff-" id="SE-b3d4b46e-1a54-4045-999b-577e7c4e4c2d" style="">​</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-97b593ec-7b9e-4800-8bc6-06a1f52f1f6b" style=""><span class="se-fs- se-ff-" id="SE-25aac43b-d055-4a39-84a1-78467c93c7da" style="">VRchat이 다른 디스크에 설치 돼어 있을 때 SDK는 오큘러스같은 다른 VRchat exe를 찾게 돼고</span></p><!-- } SE-TEXT --><!-- SE-TEXT { --><p class="se-text-paragraph se-text-paragraph-align-" id="SE-126bb1e7-f1e1-4e65-93e8-bc2346569847" style=""><span class="se-fs- se-ff-" id="SE-b449c2a4-1752-429f-8306-68852a9029ed" style="">그로 인해 문제가 생긴 듯 하다.</span></p><!-- } SE-TEXT -->
</div>
</div>
</div>
</div> </div>
</div>
</div>
--
layout: post
Title: "http协议的缓存头策略"
Date: 2013-03-11 19:33
comments: true
categories: notes
--

####http协议的缓存头策略

以下头均指返回给浏览器的响应头！

last-modify  告诉浏览器此文件的最后修改时间，浏览器在下次访问同样文件时会带上这个修改时间，服务器在收到请求后比较，如果无变化则直接返回304告诉浏览器内容无变化，使用自己本地缓存即可，通常web服务器都会自动为静态请求返回这个头!  


etag  用处以及算法基本和last-modify一样，只是为了弥补，当浏览器和服务器间通过负载均衡由多台服务器提供服务时，有可能各服务器时间并不能达到完全一致，导致last-modify头内容可能失效！ 通常服务器用etag时，它的值就是一个能唯一标示文件改动，比如md5值！

expires： 服务器返回响应的时候，包含expires头，用来告诉浏览器，这个文件请求在多少时间内直接使用浏览器本地缓存，只要在此时间内，当浏览器再次需要这个文件时，将直接使用本地换成，连http请求都省略了，由于比last-modify和etag少了http建立连接和响应的开销，所以更快。

cache-control：  由于expires头存在一个问题，就是当服务器时间和pc时间相差，假如一个文件的expires时间是1小时，此时碰巧浏览器本地时间比web服务器要慢1小时，那实际上expires头根本起不到作用。

所以http1.1协议，假如了cache-control头，内容是： cache-control: max-age=3600,  这样浏览器对待文件缓存时，使用的是相对时间。弥补了expires头的问题.
完
